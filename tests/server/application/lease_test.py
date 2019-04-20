from gumo.core.injector import injector

from gumo.pullqueue.server.application.enqueue import enqueue
from gumo.pullqueue.server.application.repository import GumoPullTaskRepository
from gumo.pullqueue.server.application.lease import LeaseTasksService
from gumo.pullqueue.server.application.lease import DeleteTasksService


def test_lease_tasks_service():
    repo = injector.get(GumoPullTaskRepository)  # type: GumoPullTaskRepository
    service = injector.get(LeaseTasksService)  # type: LeaseTasksService

    repo.purge()

    task = enqueue(
        payload={'key': 'value'},
        queue_name='server',
    )

    tasks = service.lease_tasks(
        queue_name='server',
        lease_time=3600,
        lease_size=1,
    )

    assert len(tasks) == 1
    assert tasks[0] == task


def test_delete_tasks_service():
    repo = injector.get(GumoPullTaskRepository)  # type: GumoPullTaskRepository
    lease_service = injector.get(LeaseTasksService)  # type: LeaseTasksService
    delete_service = injector.get(DeleteTasksService)  # type: DeleteTasksService

    repo.purge()

    task = enqueue(
        payload={'key': 'value'},
        queue_name='server',
    )

    assert len(lease_service.lease_tasks(
        queue_name='server',
        lease_time=3600,
        lease_size=100
    )) == 1

    delete_service.delete_tasks([task.key])

    assert len(lease_service.lease_tasks(
        queue_name='server',
        lease_time=3600,
        lease_size=100
    )) == 0
