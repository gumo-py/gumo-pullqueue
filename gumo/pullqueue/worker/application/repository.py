from injector import inject

from logging import getLogger
from typing import List

from gumo.core import EntityKey
from gumo.pullqueue import PullTask
from gumo.pullqueue.worker.domain.configuration import PullQueueWorkerConfiguration

logger = getLogger(__name__)


class PullTaskRemoteRepository:
    @inject
    def __init__(
            self,
            configuration: PullQueueWorkerConfiguration,
    ):
        self._configuration = configuration

    def lease_tasks(
            self,
            queue_name: str,
            size: int = 100,
    ) -> List[PullTask]:
        raise NotImplementedError()

    def delete_tasks(
            self,
            queue_name: str,
            keys: List[EntityKey],
    ):
        raise NotImplementedError()
