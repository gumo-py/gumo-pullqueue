from gumo.core.injector import injector

from gumo.pullqueue_worker.application import LeaseTasksService


def test_lease_service():
    service = injector.get(NotImplemented)  # type: LeaseTasksService

    assert service.lease_tasks(
        queue_name='pullqueue',
        lease_time=3600,
        lease_size=10
    ) == None
