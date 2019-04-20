from gumo.core.injector import injector

from gumo.pullqueue.worker.application.service import LeaseTasksService


def test_lease_service():
    service = injector.get(LeaseTasksService)  # type: LeaseTasksService

    assert service.lease_tasks(
        queue_name='server',
        lease_time=3600,
        lease_size=10
    ) == []
