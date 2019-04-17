import dataclasses
import datetime
import enum
from typing import Optional
from typing import List

from gumo.core import EntityKey


@dataclasses.dataclass(frozen=True)
class PullTask:
    """
    Task payload to process at enqueue time and lease time
    """
    key: EntityKey
    queue_name: str
    payload: Optional[dict] = dataclasses.field(default_factory=dict)
    schedule_time: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.utcnow)
    created_at: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.utcnow)
    tag: Optional[str] = None

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.key == other.key


@dataclasses.dataclass(frozen=True)
class PullTaskWorker:
    address: str
    name: str


class PullTaskStatus(enum.Enum):
    initial = 'initial'
    available = 'available'
    leased = 'leased'
    deleted = 'deleted'

    @classmethod
    def get(cls, name: str):
        try:
            return cls(name)
        except ValueError:
            return cls.initial


@dataclasses.dataclass(frozen=True)
class PullTaskState:
    status: PullTaskStatus = PullTaskStatus.initial
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
class PullTaskLog:
    action: str
    event_at: datetime.datetime
    worker: PullTaskWorker
    payload: dict


@dataclasses.dataclass(frozen=True)
class GumoPullTask:
    """
    A class containing payload and metadata used internally in the Pull Queue.
    """
    KIND = 'GumoPullTask'

    task: PullTask
    state: PullTaskState
    logs: List[PullTaskLog]

    @property
    def key(self) -> EntityKey:
        return self.task.key

    def _clone(self, **changes):
        return dataclasses.replace(self, **changes)

    def with_status(self, new_status: PullTaskStatus):
        return self._clone(
            state=self.state.with_status(new_status=new_status)
        )
