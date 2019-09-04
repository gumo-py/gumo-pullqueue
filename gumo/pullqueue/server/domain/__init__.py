import copy
import dataclasses
import datetime
import enum
from typing import List

from typing import Optional

from gumo.core import EntityKey

from gumo.pullqueue import PullTask
from gumo.pullqueue.server.domain.event import TaskEvent


@dataclasses.dataclass(frozen=True)
class PullTaskWorker:
    address: str
    name: str

    def to_json(self) -> dict:
        return {
            'address': self.address,
            'name': self.name,
        }

    @classmethod
    def get_server(cls):
        return cls(
            address='server',
            name='server'
        )


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
class GumoPullTask:
    """
    A class containing payload and metadata used internally in the Pull Queue.
    """
    KIND = 'GumoPullTask'

    task: PullTask
    state: PullTaskState
    event_logs: List[TaskEvent] = dataclasses.field(default_factory=list)

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
