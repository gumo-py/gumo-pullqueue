from gumo.core.injector import injector

from gumo.pullqueue.application.enqueue import enqueue
from gumo.pullqueue.application.repository import GumoPullTaskRepository
from gumo.pullqueue.application.lease import LeaseTasksService


def test_lease_tasks_service():
    repo = injector.get(GumoPullTaskRepository)  # type: GumoPullTaskRepository
    service = injector.get(LeaseTasksService)  # type: LeaseTasksService

    repo.purge()

    task = enqueue(
        payload={'key': 'value'},
        queue_name='pullqueue',
    )

    tasks = service.lease_tasks(
        queue_name='pullqueue',
        lease_time=3600,
        lease_size=1,
    )

    assert len(tasks) == 1
    assert tasks[0] == task
