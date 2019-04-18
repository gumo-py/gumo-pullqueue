from logging import getLogger
from typing import List

from gumo.core import EntityKey
from gumo.pullqueue import PullTask
from gumo.pullqueue_worker import PullQueueWorkerConfiguration

logger = getLogger(__name__)


class PullTaskRemoteRepository:
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
            keys: List[EntityKey],
    ):
        raise NotImplementedError()
