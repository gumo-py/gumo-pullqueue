from gumo.core.injector import injector

from gumo.pullqueue.server.application.enqueue import enqueue
from gumo.pullqueue.server.application.repository import GumoPullTaskRepository
from gumo.pullqueue.server.domain import PullTaskWorker
from gumo.pullqueue.server.application.lease import FetchAvailableTasksService
from gumo.pullqueue.server.application.lease import LeaseTaskService
from gumo.pullqueue.server.application.lease import FinalizeTaskService


def test_lease_tasks_service():
    repo = injector.get(GumoPullTaskRepository)  # type: GumoPullTaskRepository
    fetch_service = injector.get(FetchAvailableTasksService)  # type: FetchAvailableTasksService
    service = injector.get(LeaseTaskService)  # type: LeaseTaskService

    repo.purge()

    task = enqueue(
        payload={'key': 'value'},
        queue_name='server',
    )

    tasks = fetch_service.fetch_tasks(
        queue_name='server',
        lease_size=1,
    )

    leased_task = service.lease_task(
        queue_name='server',
        lease_time=3600,
        key=tasks[0].key,
        worker=PullTaskWorker(address='test', name='test-worker'),
    )

    assert leased_task == task


def test_delete_tasks_service():
    repo = injector.get(GumoPullTaskRepository)  # type: GumoPullTaskRepository
    fetch_service = injector.get(FetchAvailableTasksService)  # type: FetchAvailableTasksService
    lease_service = injector.get(LeaseTaskService)  # type: LeaseTaskService
    delete_service = injector.get(FinalizeTaskService)  # type: FinalizeTaskService

    repo.purge()

    task = enqueue(
        payload={'key': 'value'},
        queue_name='server',
    )

    assert len(fetch_service.fetch_tasks(
        queue_name='server',
        lease_size=10,
    )) == 1

    leased_task = lease_service.lease_task(
        queue_name='server',
        lease_time=3600,
        key=task.key,
        worker=PullTaskWorker(address='test', name='test-worker'),
    )

    assert leased_task.key == task.key

    delete_service.finalize_task(
        queue_name='server',
        task_keys=[task.key],
    )

    assert len(fetch_service.fetch_tasks(
        queue_name='server',
        lease_size=10,
    )) == 0
