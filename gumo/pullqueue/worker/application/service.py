from logging import getLogger

from typing import List
from typing import Optional

from injector import inject

from gumo.pullqueue import PullTask
from gumo.pullqueue.worker.application.repository import PullTaskRemoteRepository

logger = getLogger(__name__)


class LeaseTasksService:
    @inject
    def __init__(
            self,
            repository: PullTaskRemoteRepository,
    ):
        self._repository = repository

    def lease_tasks(
            self,
            queue_name: str,
            lease_time: int,
            lease_size: int,
            tag: Optional[str] = None,
    ) -> List[PullTask]:
        tasks = self._repository.lease_tasks(
            queue_name=queue_name,
            size=lease_size,
        )

        return tasks


class DeleteTasksService:
    @inject
    def __init__(
            self,
            repository: PullTaskRemoteRepository,
    ):
        self._repository = repository

    def delete_tasks(
            self,
            tasks: List[PullTask],
    ):
        if len(tasks) == 0:
            logger.debug(f'delete_tasks called with empty lists.')
            return

        queue_names = list(set([task.queue_name for task in tasks]))
        if len(queue_names) > 1:
            raise ValueError(f'A mix of tasks from different queues: {queue_names}')

        queue_name = queue_names[0]
        keys = [task.key for task in tasks]
        response = self._repository.delete_tasks(
            queue_name=queue_name,
            keys=keys,
        )
        logger.debug(f'delete_tasks response: {response}')
