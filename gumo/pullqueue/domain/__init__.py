import dataclasses
import datetime
from typing import Optional
from typing import List

from gumo.core import EntityKey


@dataclasses.dataclass(frozen=True)
class PullTask:
    """
    Task payload to process at enqueue time and lease time
    """
    key: EntityKey
    payload: Optional[dict] = dataclasses.field(default_factory=dict)
    schedule_time: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.utcnow)
    created_at: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.utcnow)
    queue_name: Optional[str] = None
    tag: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class PullTaskWorker:
    address: str
    name: str


@dataclasses.dataclass(frozen=True)
class PullTaskState:
    execution_count: int = 0
    retry_count: int = 0
    last_executed_at: Optional[datetime.datetime] = None
    next_executed_at: Optional[datetime.datetime] = None
    leased_at: Optional[datetime.datetime] = None
    lease_expires_at: Optional[datetime.datetime] = None
    leased_by: Optional[PullTaskWorker] = None


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
