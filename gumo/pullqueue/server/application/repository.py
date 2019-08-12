import datetime
from typing import List
from typing import Optional

from gumo.core import EntityKey
from gumo.pullqueue.server.domain import GumoPullTask


class GumoPullTaskRepository:
    def save(
            self,
            pulltask: GumoPullTask
    ):
        raise NotImplementedError()

    def fetch_available_tasks(
            self,
            queue_name: str,
            tag: Optional[str] = None,
            size: int = 100,
            now: Optional[datetime.datetime] = None,
    ) -> List[GumoPullTask]:
        raise NotImplementedError()

    def total_count(self) -> int:
        raise NotImplementedError()

    def purge(self):
        raise NotImplementedError()

    def fetch(self, key: EntityKey) -> Optional[GumoPullTask]:
        tasks = self.fetch_keys(keys=[key])
        return tasks[0]

    def fetch_keys(self, keys: List[EntityKey]) -> List[GumoPullTask]:
        raise NotImplementedError()

    def put_multi(self, tasks: List[GumoPullTask]):
        raise NotImplementedError()

    def fetch_lease_expired_tasks(
            self,
            now: Optional[datetime.datetime] = None,
    ) -> List[GumoPullTask]:
        raise NotImplementedError()
