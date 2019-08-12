import datetime

from logging import getLogger
from injector import inject
from typing import Optional

from gumo.core import EntityKey
from gumo.datastore import datastore_transaction
from gumo.pullqueue.server.application.repository import GumoPullTaskRepository
from gumo.pullqueue import PullTask
from gumo.pullqueue.server.domain import PullTaskWorker
from gumo.pullqueue.server.domain import LeaseRequest
from gumo.pullqueue.server.domain import SuccessRequest
from gumo.pullqueue.server.domain import FailureRequest


logger = getLogger(__name__)


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
