import dataclasses
import datetime
import enum
import copy

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
        return dataclasses.replace(self, **changes)

    def with_status(self, new_status: PullTaskStatus):
        return self._clone(
            status=new_status,
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
class LeaseRequest(TaskEvent):
    lease_time: int

    def to_json(self) -> dict:
        j = super(self).to_json()
        j['lease_time'] = self.lease_time
        return j


@dataclasses.dataclass(frozen=True)
class LeaseExtendRequest(TaskEvent):
    lease_extend_time: int

    def to_json(self) -> dict:
        j = super(self).to_json()
        j['lease_extend_time'] = self.lease_extend_time
        return j


@dataclasses.dataclass(frozen=True)
class SuccessRequest(TaskEvent):
    pass


@dataclasses.dataclass(frozen=True)
class FailureRequest(TaskEvent):
    message: str

    def to_json(self) -> dict:
        j = super(self).to_json()
        j['message'] = self.message
        return j


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
        return dataclasses.replace(self, **changes)

    def with_status(self, new_status: PullTaskStatus):
        return self._clone(
            state=self.state.with_status(new_status=new_status)
        )
