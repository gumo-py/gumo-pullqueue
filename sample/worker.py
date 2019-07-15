import sys
import logging

from gumo.core.injector import injector
from gumo.pullqueue.worker import configure as pullqueue_worker_configure
from gumo.pullqueue.worker.application.service import LeaseTasksService
from gumo.pullqueue.worker.application.service import DeleteTasksService

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


pullqueue_worker_configure(
    server_url='http://server:8080',
)


if __name__ == '__main__':
    import time

    lease_service = injector.get(LeaseTasksService)  # type: LeaseTasksService
    delete_service = injector.get(DeleteTasksService)  # type: DeleteTasksService

    while True:
        tasks = lease_service.lease_tasks(
            queue_name='pullqueue',
            lease_time=3600,
            lease_size=1,
        )
        print(tasks)

        if len(tasks) > 0:
            task = tasks[0]
            print('#####')
            print(task.payload)
            print('#####')
            delete_service.delete_tasks(tasks=[task])
            time.sleep(1)
        else:
            time.sleep(10)
