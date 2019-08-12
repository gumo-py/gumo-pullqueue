from logging import getLogger

from typing import List
from typing import Optional

from injector import inject

from gumo.pullqueue import PullTask
from gumo.pullqueue.worker.application.repository import PullTaskRemoteRepository

logger = getLogger(__name__)


class FetchAvailableTasksService:
    @inject
    def __init__(
            self,
            repository: PullTaskRemoteRepository,
    ):
        self._repository = repository

    def available_tasks(
            self,
            queue_name: str,
            lease_size: int,
            tag: Optional[str] = None,
    ) -> List[PullTask]:
        tasks = self._repository.available_tasks(
            queue_name=queue_name,
            size=lease_size,
            tag=tag,
        )

        return tasks

class LeaseTaskService:
    @inject
    def __init__(
            self,
            repository: PullTaskRemoteRepository,
    ):
        self._repository = repository

    def lease_task(
            self,
            queue_name: str,
            task: PullTask,
            lease_time: int,
    ) -> PullTask:
        task = self._repository.lease_task(
            queue_name=queue_name,
            task=task,
            lease_time=lease_time,
        )

        return task


class FinalizeTaskService:
    @inject
    def __init__(
            self,
            repository: PullTaskRemoteRepository,
    ):
        self._repository = repository

    def finalize_task(
            self,
            task: PullTask,
    ):
        response = self._repository.finalize_task(
            queue_name=task.queue_name,
            key=task.key,
        )
        logger.debug(f'delete_tasks response: {response}')
