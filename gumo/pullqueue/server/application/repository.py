import datetime
from injector import inject
from typing import List
from typing import Optional

from gumo.core import GumoConfiguration
from gumo.core import EntityKey
from gumo.datastore.domain.configuration import DatastoreConfiguration
from gumo.pullqueue.server.domain.configuration import PullQueueConfiguration
from gumo.pullqueue.server.domain import GumoPullTask


class GumoPullTaskRepository:
    @inject
    def __init__(
            self,
            gumo_configuration: GumoConfiguration,
            datastore_configuration: DatastoreConfiguration,
            pullqueue_configuration: PullQueueConfiguration,
    ):
        self._gumo_configuration = gumo_configuration
        self._datastore_configuration = datastore_configuration
        self._pullqueue_configuration = pullqueue_configuration

    def save(
            self,
            pulltask: GumoPullTask
    ):
        raise NotImplementedError()

    def multi_save(
            self,
            tasks: List[GumoPullTask],
    ):
        raise NotImplementedError()

    def fetch_available_tasks(
            self,
            queue_name: str,
            size: int = 100,
            now: Optional[datetime.datetime] = None,
    ) -> List[GumoPullTask]:
        raise NotImplementedError()

    def total_count(self) -> int:
        raise NotImplementedError()

    def purge(self):
        raise NotImplementedError()

    def fetch_keys(self, keys: List[EntityKey]) -> List[GumoPullTask]:
        raise NotImplementedError()

    def put_multi(self, tasks: List[GumoPullTask]):
        raise NotImplementedError()
