from injector import inject
from typing import List

from gumo.core import GumoConfiguration
from gumo.datastore.domain.configuration import DatastoreConfiguration
from gumo.pullqueue.domain.configuration import PullQueueConfiguration
from gumo.pullqueue.domain import GumoPullTask


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
            size: int = 100,
    ) -> List[GumoPullTask]:
        raise NotImplementedError()

    def total_count(self) -> int:
        raise NotImplementedError()
