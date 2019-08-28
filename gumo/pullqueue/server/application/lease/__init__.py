import datetime

from logging import getLogger
from injector import inject
from typing import Optional
from typing import List

from gumo.core import EntityKey
from gumo.datastore import datastore_transaction
from gumo.pullqueue.server.application.repository import GumoPullTaskRepository
from gumo.pullqueue import PullTask
from gumo.pullqueue.server.domain import PullTaskWorker
from gumo.pullqueue.server.domain import LeaseRequest
from gumo.pullqueue.server.domain import LeaseExtendRequest
from gumo.pullqueue.server.domain import SuccessRequest
from gumo.pullqueue.server.domain import FailureRequest
from gumo.pullqueue.server.domain import LeaseExpired


logger = getLogger(__name__)


class CheckLeaseExpiredTasksService:
    @inject
    def __init__(
            self,
            repository: GumoPullTaskRepository
    ):
        self._repository = repository

    def check_and_update_expired_tasks(
            self,
            now: Optional[datetime.datetime] = None,
    ) -> List[PullTask]:
        lease_expired_tasks = self._repository.fetch_lease_expired_tasks(now=now)

        if len(lease_expired_tasks) == 0:
            logger.debug(f'Lease expired tasks are not found.')
            return []

        if now is None:
            now = datetime.datetime.utcnow()

        event = LeaseExpired(
            event_at=now,
            worker=PullTaskWorker.get_server(),
        )

        updated_tasks = [
            event.build_next(task=task) for task in lease_expired_tasks
        ]

        self._repository.put_multi(tasks=updated_tasks)

        return [task.task for task in updated_tasks]


class FetchAvailableTasksService:
    @inject
    def __init__(
            self,
            repository: GumoPullTaskRepository,
    ):
        self._repository = repository

    def fetch_tasks(
            self,
            queue_name: str,
            lease_size: int,
            tag: Optional[str] = None,
    ):
        tasks = self._repository.fetch_available_tasks(
            queue_name=queue_name,
            size=lease_size,
            tag=tag,
        )

        return [task.task for task in tasks]


class LeaseTaskService:
    @inject
    def __init__(
            self,
            repository: GumoPullTaskRepository,
    ):
        self._repository = repository

    def lease_task(
            self,
            queue_name: str,
            lease_time: int,
            key: EntityKey,
            worker: PullTaskWorker,
    ) -> PullTask:
        now = datetime.datetime.utcnow()
        task = self._repository.fetch(key=key)

        if task is None:
            raise ValueError(f'Task not found (key={key.key_literal()})')

        if task.task.queue_name != queue_name:
            raise ValueError(f'Invalid queue_name={queue_name}, mismatch to {task.task}')

        event = LeaseRequest(
            event_at=now,
            worker=worker,
            lease_time=lease_time,
        )
        leased_task = event.build_next(task)

        self._repository.save(leased_task)
        return leased_task.task


class LeaseExtendTaskService:
    @inject
    def __init__(
            self,
            repository: GumoPullTaskRepository,
    ):
        self._repository = repository

    def lease_extend_task(
            self,
            queue_name: str,
            lease_extend_time: int,
            key: EntityKey,
            worker: PullTaskWorker,
    ) -> PullTask:
        now = datetime.datetime.utcnow()
        task = self._repository.fetch(key=key)

        if task is None:
            raise ValueError(f'Task not found (key={key.key_literal()})')

        if task.task.queue_name != queue_name:
            raise ValueError(f'Invalid queue_name={queue_name}, mismatch to {task.task}')

        event = LeaseExtendRequest(
            event_at=now,
            worker=worker,
            lease_extend_time=lease_extend_time,
        )
        lease_extended_task = event.build_next(task=task)

        self._repository.save(lease_extended_task)
        return lease_extended_task.task


class FinalizeTaskService:
    @inject
    def __init__(
            self,
            repository: GumoPullTaskRepository,
    ):
        self._repository = repository

    @datastore_transaction()
    def finalize_task(
            self,
            queue_name: str,
            key: EntityKey,
            worker: PullTaskWorker,
    ) -> PullTask:
        now = datetime.datetime.utcnow()
        task = self._repository.fetch(key=key)

        if task is None:
            raise ValueError(f'Task({key.key_literal()}) does not found.')

        if task.task.queue_name != queue_name:
            raise ValueError(f'Task queue_name is mismatched. (expected: {queue_name}, but received {task.task}')

        event = SuccessRequest(
            event_at=now,
            worker=worker,
        )
        succeeded_task = event.build_next(task)
        self._repository.save(succeeded_task)

        return succeeded_task.task


class FailureTaskService:
    @inject
    def __init__(
            self,
            repository: GumoPullTaskRepository,
    ):
        self._repository = repository

    @datastore_transaction()
    def failure_task(
            self,
            queue_name: str,
            key: EntityKey,
            message: str,
            worker: PullTaskWorker,
    ) -> PullTask:
        now = datetime.datetime.utcnow()
        task = self._repository.fetch(key=key)

        if task is None:
            raise ValueError(f'Task({key.key_literal()}) does not found.')

        if task.task.queue_name != queue_name:
            raise ValueError(f'Task queue_name is mismatched. (expected: {queue_name}, but received {task.task}')

        event = FailureRequest(
            event_at=now,
            worker=worker,
            message=message,
        )
        failure_task = event.build_next(task)
        self._repository.save(failure_task)

        return failure_task.task
