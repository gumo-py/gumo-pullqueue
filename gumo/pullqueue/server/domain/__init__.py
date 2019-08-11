import dataclasses
import datetime
import enum
import copy
import random

from typing import Optional
from typing import List

from gumo.core import EntityKey
from gumo.pullqueue.domain import PullTask


@dataclasses.dataclass(frozen=True)
class PullTaskWorker:
    address: str
    name: str

    def to_json(self) -> dict:
        return {
            'address': self.address,
            'name': self.name,
        }


class PullTaskStatus(enum.Enum):
    available = 'available'
    leased = 'leased'
    deleted = 'deleted'

    @classmethod
    def get(cls, name: str):
        try:
            return cls(name)
        except ValueError:
            return cls.available


@dataclasses.dataclass(frozen=True)
class PullTaskState:
    status: PullTaskStatus = PullTaskStatus.available
    execution_count: int = 0
    retry_count: int = 0
    last_executed_at: Optional[datetime.datetime] = None
    next_executed_at: Optional[datetime.datetime] = None
    leased_at: Optional[datetime.datetime] = None
    lease_expires_at: Optional[datetime.datetime] = None
    leased_by: Optional[PullTaskWorker] = None

    def _clone(self, **changes):
        """
        :rtype: PullTaskState
        """
        return dataclasses.replace(self, **changes)

    def with_status(self, new_status: PullTaskStatus):
        """
        :rtype: PullTaskState
        """
        return self._clone(
            status=new_status,
        )

    def with_lease_info(
            self,
            leased_at: Optional[datetime.datetime],
            lease_expires_at: Optional[datetime.datetime],
            leased_by: Optional[PullTaskWorker],
    ):
        """
        :rtype: PullTaskState
        """
        return self._clone(
            leased_at=leased_at,
            lease_expires_at=lease_expires_at,
            leased_by=leased_by,
        )

    def increment_count_if_needed(self):
        """
        :rtype: PullTaskState
        """
        return self._clone(
            execution_count=self.execution_count + 1,
            retry_count=self.retry_count + 1 if self.execution_count > 0 else 0
        )

    def with_schedules(
            self,
            last_executed_at: datetime.datetime,
            next_executed_at: datetime.datetime
    ):
        """
        :rtype: PullTaskState
        """
        return self._clone(
            last_executed_at=last_executed_at,
            next_executed_at=next_executed_at,
        )


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
    def load_json(cls, j: dict):
        clazz = None
        event_name = j.get('event_name')
        for c in cls.__subclasses__():
            if event_name == c.__name__:
                clazz = c
                break
        if clazz is None:
            raise ValueError(f'Invalid event_name={event_name}')

        j = copy.copy(j)
        del j['event_name']
        return clazz(**j)


@dataclasses.dataclass(frozen=True)
class GumoPullTask:
    """
    A class containing payload and metadata used internally in the Pull Queue.
    """
    KIND = 'GumoPullTask'

    task: PullTask
    state: PullTaskState
    event_logs: List[TaskEvent]

    @property
    def key(self) -> EntityKey:
        return self.task.key

    def _clone(self, **changes):
        """
        :rtype: GumoPullTask
        """
        return dataclasses.replace(self, **changes)

    def with_status(self, new_status: PullTaskStatus):
        """
        :rtype: GumoPullTask
        """
        return self._clone(
            state=self.state.with_status(new_status=new_status)
        )

    def with_state(self, new_state: PullTaskState):
        """
        :rtype: GumoPullTask
        """
        return self._clone(
            state=new_state
        )

    def add_event_log(self, event_log: TaskEvent):
        """
        :rtype: GumoPullTask
        """
        event_logs = copy.copy(self.event_logs)
        event_logs.append(event_log)
        return self._clone(
            event_logs=event_logs
        )


@dataclasses.dataclass(frozen=True)
class LeaseRequest(TaskEvent):
    lease_time: int

    def to_json(self) -> dict:
        j = super(self).to_json()
        j['lease_time'] = self.lease_time
        return j

    def build_next(self, task: GumoPullTask) -> GumoPullTask:
        if task.state.status == PullTaskStatus.deleted:
            raise ValueError(f'Target task can not change status, because already deleted.')

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
        j = super(self).to_json()
        j['lease_extend_time'] = self.lease_extend_time
        return j

    def build_next(self, task: GumoPullTask) -> GumoPullTask:
        if task.state.status == PullTaskStatus.deleted:
            raise ValueError(f'Target task can not change status, because already deleted.')

        if task.state.status != PullTaskStatus.leased:
            raise ValueError(f'Target task status must equal as leased, but got: {task.state.status}')

        new_state = task.state.with_lease_info(
            leased_at=task.state.leased_at,
            lease_expires_at=task.state.lease_expires_at + datetime.timedelta(seconds=self.lease_extend_time),
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
        j = super(self).to_json()
        j['message'] = self.message
        return j

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
