import dataclasses
import datetime
import random

from typing import Optional

from gumo.pullqueue import PullTask
from gumo.pullqueue.server.domain import GumoPullTask
from gumo.pullqueue.server.domain import PullTaskState
from gumo.pullqueue.server.domain import PullTaskStatus
from gumo.pullqueue.server.domain import PullTaskWorker

from gumo.pullqueue.server.domain.exception import AlreadyLeasedError
from gumo.pullqueue.server.domain.exception import AlreadyDeletedError


@dataclasses.dataclass(frozen=True)
class TaskEvent:
    event_at: datetime.datetime
    worker: PullTaskWorker

    def to_json(self) -> dict:
        return {
            'event_name': self.__class__.__name__,
            'event_at': self.event_at.isoformat(),
            'worker': self.worker.to_json(),
        }

    @classmethod
    def from_json(cls, j: dict):
        clazz = None
        event_name = j.get('event_name')
        for c in cls.__subclasses__():
            if event_name == c.__name__:
                clazz = c
                break
        if clazz is None:
            raise ValueError(f'Invalid event_name={event_name}')

        return clazz(**clazz.load_params(j))

    @classmethod
    def load_params(cls, j: dict) -> dict:
        return {
            'event_at': datetime.datetime.fromisoformat(j['event_at']),
            'worker': PullTaskWorker(
                address=j['worker']['address'],
                name=j['worker']['name'],
            )
        }


@dataclasses.dataclass(frozen=True)
class EnqueueRequest(TaskEvent):
    def build_next(self, pulltask: PullTask) -> GumoPullTask:
        new_state = PullTaskState(
            status=PullTaskStatus.available,
            next_executed_at=pulltask.schedule_time,
        )

        return GumoPullTask(
            task=pulltask,
            state=new_state,
            event_logs=[self]
        )


@dataclasses.dataclass(frozen=True)
class LeaseRequest(TaskEvent):
    lease_time: int

    def to_json(self) -> dict:
        j = super(LeaseRequest, self).to_json()
        j['lease_time'] = self.lease_time
        return j

    @classmethod
    def load_params(cls, j: dict) -> dict:
        params = super(LeaseRequest, cls).load_params(j)
        params['lease_time'] = j['lease_time']
        return params

    def build_next(self, task: GumoPullTask) -> GumoPullTask:
        if task.state.status == PullTaskStatus.deleted:
            raise AlreadyDeletedError(f'{task.key.key_literal()} is already deleted.')

        if task.state.status == PullTaskStatus.leased:
            raise AlreadyLeasedError(f'{task.key.key_literal()} is already leased.')

        new_state = task.state.with_status(
            new_status=PullTaskStatus.leased
        ).with_lease_info(
            leased_at=self.event_at,
            lease_expires_at=self.event_at + datetime.timedelta(seconds=self.lease_time),
            leased_by=self.worker,
        ).increment_count_if_needed()

        next_task = task.with_state(
            new_state=new_state
        ).add_event_log(
            event_log=self
        )

        return next_task


@dataclasses.dataclass(frozen=True)
class LeaseExtendRequest(TaskEvent):
    lease_extend_time: int

    def to_json(self) -> dict:
        j = super(LeaseExtendRequest, self).to_json()
        j['lease_extend_time'] = self.lease_extend_time
        return j

    @classmethod
    def load_params(cls, j: dict) -> dict:
        params = super(LeaseExtendRequest, cls).load_params(j)
        params['lease_extend_time'] = j['lease_extend_time']
        return params

    def build_next(self, task: GumoPullTask, now: Optional[datetime.datetime] = None) -> GumoPullTask:
        if task.state.status == PullTaskStatus.deleted:
            raise ValueError(f'Target task can not change status, because already deleted.')

        if task.state.status != PullTaskStatus.leased:
            raise ValueError(f'Target task status must equal as leased, but got: {task.state.status}')

        if now is None:
            now = datetime.datetime.utcnow()

        new_state = task.state.with_lease_info(
            leased_at=task.state.leased_at,
            lease_expires_at=now + datetime.timedelta(seconds=self.lease_extend_time),
            leased_by=task.state.leased_by,
        )

        next_task = task.with_state(
            new_state=new_state
        ).add_event_log(
            event_log=self
        )

        return next_task


@dataclasses.dataclass(frozen=True)
class SuccessRequest(TaskEvent):
    def build_next(self, task: GumoPullTask) -> GumoPullTask:
        if task.state.status == PullTaskStatus.deleted:
            raise ValueError(f'Target task can not change status, because already deleted.')

        if task.state.status != PullTaskStatus.leased:
            raise ValueError(f'Target task status must equal as leased, but got: {task.state.status}')

        new_state = task.state.with_status(
            new_status=PullTaskStatus.deleted
        )

        next_task = task.with_state(
            new_state=new_state
        ).add_event_log(
            event_log=self
        )

        return next_task


def exponential_back_off_with_jitters(
        base_sleep_seconds: int,
        attempts: int,
        max_sleep_seconds: int,
) -> int:
    # The sleep time is an exponentially-increasing function of base_sleep_seconds.
    # But, it never exceeds max_sleep_seconds.
    sleep_seconds = min([base_sleep_seconds * (2 ** (attempts - 1)), max_sleep_seconds])
    # Randomize to a random value in the range sleep_seconds/2 .. sleep_seconds
    sleep_seconds = sleep_seconds * (0.5 * (1 + random.random()))
    # But never sleep less than base_sleep_seconds
    sleep_seconds = max(base_sleep_seconds, sleep_seconds)

    return sleep_seconds


@dataclasses.dataclass(frozen=True)
class FailureRequest(TaskEvent):
    message: str

    def to_json(self) -> dict:
        j = super(FailureRequest, self).to_json()
        j['message'] = self.message
        return j

    @classmethod
    def load_params(cls, j: dict) -> dict:
        params = super(FailureRequest, cls).load_params(j)
        params['message'] = j['message']
        return params

    def build_next(
            self,
            task: GumoPullTask,
            now: Optional[datetime.datetime] = None,
    ) -> GumoPullTask:
        if task.state.status == PullTaskStatus.deleted:
            raise ValueError(f'Target task can not change status, because already deleted.')

        if task.state.status != PullTaskStatus.leased:
            raise ValueError(f'Target task status must equal as leased, but got: {task.state.status}')

        if now is None:
            now = datetime.datetime.utcnow()

        sleep_seconds = exponential_back_off_with_jitters(
            base_sleep_seconds=60,
            attempts=task.state.execution_count,
            max_sleep_seconds=3600 * 24,
        )

        new_state = task.state.with_status(
            new_status=PullTaskStatus.available
        ).with_lease_info(
            leased_at=None,
            lease_expires_at=None,
            leased_by=None,
        ).with_schedules(
            last_executed_at=task.state.leased_at,
            next_executed_at=now + datetime.timedelta(seconds=sleep_seconds)
        )

        next_task = task.with_state(
            new_state=new_state
        ).add_event_log(
            event_log=self
        )

        return next_task


@dataclasses.dataclass(frozen=True)
class LeaseExpired(TaskEvent):
    def build_next(
            self,
            task: GumoPullTask,
            now: Optional[datetime.datetime] = None,
    ) -> GumoPullTask:
        if task.state.status != PullTaskStatus.leased:
            raise ValueError(f'Target task must be status as `leased`, but expected {task.state.status.value}')

        if now is None:
            now = datetime.datetime.utcnow()

        sleep_seconds = exponential_back_off_with_jitters(
            base_sleep_seconds=60,
            attempts=task.state.execution_count,
            max_sleep_seconds=3600 * 24,
        )

        new_state = task.state.with_status(
            new_status=PullTaskStatus.available
        ).with_lease_info(
            leased_at=None,
            lease_expires_at=None,
            leased_by=None,
        ).with_schedules(
            last_executed_at=task.state.leased_at,
            next_executed_at=now + datetime.timedelta(seconds=sleep_seconds)
        )

        next_task = task.with_state(
            new_state=new_state
        ).add_event_log(
            event_log=self
        )

        return next_task
