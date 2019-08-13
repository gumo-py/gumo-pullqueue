import sys
import logging
import datetime

from gumo.core.injector import injector
from gumo.pullqueue.worker import configure as pullqueue_worker_configure
from gumo.pullqueue.worker.application.service import FetchAvailableTasksService
from gumo.pullqueue.worker.application.service import LeaseTaskService
from gumo.pullqueue.worker.application.service import FinalizeTaskService
from gumo.pullqueue.worker.application.service import FailureTaskService
from gumo.pullqueue.worker.application.service import LeaseExtendTaskService

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


pullqueue_worker_configure(
    server_url='http://server:8080',
    request_logger=logger,
)


if __name__ == '__main__':
    import time

    queue_name = 'pullqueue'

    fetch_service: FetchAvailableTasksService = injector.get(FetchAvailableTasksService)
    lease_service: LeaseTaskService = injector.get(LeaseTaskService)
    finalize_service: FinalizeTaskService = injector.get(FinalizeTaskService)
    failure_service: FailureTaskService = injector.get(FailureTaskService)
    lease_extend_service: LeaseExtendTaskService = injector.get(LeaseExtendTaskService)

    while True:
        tasks = fetch_service.available_tasks(
            queue_name=queue_name,
            lease_size=1,
        )

        if len(tasks) == 0:
            print('available tasks are not found.')
            time.sleep(10)
            continue

        task = lease_service.lease_task(
            queue_name=queue_name,
            lease_time=60,
            task=tasks[0],
        )

        print('#####')
        print(task.payload)

        if 'fail' in task.payload and task.payload['fail']:
            failure_service.failure_task(
                task=task,
                message=f'Something failed at {datetime.datetime.utcnow().isoformat()}'
            )
            continue

        if 'extend' in task.payload and task.payload['extend']:
            time.sleep(30)
            print('lease extend ...')
            lease_extend_service.lease_extend_task(
                task=task,
                lease_extend_time=300
            )
            time.sleep(60)

        print('#####')
        finalize_service.finalize_task(task=task)
        time.sleep(1)
