from injector import inject
from typing import Optional
from typing import List

from gumo.core import EntityKey

from gumo.pullqueue.application.repository import GumoPullTaskRepository
from gumo.pullqueue.domain import PullTask


class LeaseTasksService:
    @inject
    def __init__(
            self,
            repository: GumoPullTaskRepository,
    ):
        self._repository = repository

    def lease_tasks(
            self,
            lease_time: int,
            lease_size: int,
            tag: Optional[str] = None
    ) -> List[PullTask]:
        tasks = self._repository.fetch_available_tasks(size=lease_size)

        # TODO: Update GumoPullTask for lease.
        lease_tasks = [task.task for task in tasks]

        return lease_tasks


class DeleteTasksService:
    @inject
    def __init__(
            self,
            repository: GumoPullTaskRepository,
    ):
        self._repository = repository

    def delete_tasks(
            self,
            task_keys: List[EntityKey],
    ):
        pass
