from logging import getLogger
from injector import inject
from typing import Optional
from typing import List

from gumo.core import EntityKey
from gumo.datastore import datastore_transaction
from gumo.pullqueue.server.application.repository import GumoPullTaskRepository
from gumo.pullqueue import PullTask
from gumo.pullqueue.server.domain import PullTaskStatus

logger = getLogger(__name__)


class LeaseTasksService:
    @inject
    def __init__(
            self,
            repository: GumoPullTaskRepository,
    ):
        self._repository = repository

    def lease_tasks(
            self,
            queue_name: str,
            lease_time: int,
            lease_size: int,
            tag: Optional[str] = None
    ) -> List[PullTask]:
        tasks = self._repository.fetch_available_tasks(
            queue_name=queue_name,
            size=lease_size
        )

        # TODO: Update GumoPullTask for lock and lease.

        lease_tasks = [task.task for task in tasks]
        return lease_tasks


class DeleteTasksService:
    @inject
    def __init__(
            self,
            repository: GumoPullTaskRepository,
    ):
        self._repository = repository

    @datastore_transaction()
    def delete_tasks(
            self,
            queue_name: str,
            task_keys: List[EntityKey],
    ):
        tasks = self._repository.fetch_keys(keys=task_keys)

        not_found_tasks = [t for t in tasks if t is None]
        if len(not_found_tasks) > 0:
            raise ValueError(f'Some tasks does not found.')

        other_queued_tasks = [task for task in tasks if task.task.queue_name != queue_name]
        if len(other_queued_tasks) > 0:
            raise ValueError(
                f'Some tasks belong to other queues. (target={queue_name}, other_queue_names={other_queued_tasks})'
            )

        deleted_tasks = [
            task.with_status(new_status=PullTaskStatus.deleted)
            for task in tasks
        ]
        self._repository.put_multi(deleted_tasks)
