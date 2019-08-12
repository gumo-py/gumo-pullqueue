# from gumo.core.injector import injector
#
# from gumo.pullqueue.worker.application.service import LeaseTaskService
#
#
# def test_lease_service():
#     service = injector.get(LeaseTaskService)  # type: LeaseTaskService
#
#     assert service.lease_task(
#         queue_name='server',
#         lease_time=3600,
#     ) == []
