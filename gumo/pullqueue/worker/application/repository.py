from injector import inject

from logging import getLogger
from typing import List
from typing import Optional

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

    def available_tasks(
            self,
            queue_name: str,
            size: int = 10,
            tag: Optional[str] = None,
    ) -> List[PullTask]:
        raise NotImplementedError()

    def lease_task(
            self,
            queue_name: str,
            task: PullTask,
            lease_time: int = 300,
    ) -> PullTask:
        raise NotImplementedError()

    def finalize_task(
            self,
            queue_name: str,
            key: EntityKey,
    ) -> PullTask:
        raise NotImplementedError()

    def failure_task(
            self,
            queue_name: str,
            key: EntityKey,
            message: str,
    ) -> PullTask:
        raise NotImplementedError()

    def lease_extend_task(
            self,
            queue_name: str,
            key: EntityKey,
            lease_extend_time: int,
    ) -> PullTask:
        raise NotImplementedError()
