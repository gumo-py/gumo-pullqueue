import os
import sys
import logging

from gumo.core import MockAppEngineEnvironment
from gumo.core.injector import injector
from gumo.pullqueue.worker import configure as pullqueue_worker_configure
from gumo.pullqueue.worker.application.service import LeaseTasksService
from gumo.pullqueue.worker.application.service import DeleteTasksService

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') is None:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/credential.json'

# Initialization process in development environment.
if __name__ == '__main__' or 'PYTEST' in os.environ:
    app_yaml_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'app.yaml'
    )
    MockAppEngineEnvironment.load_app_yaml(app_yaml_path=app_yaml_path)

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

        if len(tasks) > 0:
            print(tasks)
            delete_service.delete_tasks(tasks=tasks)
            time.sleep(3)
        else:
            time.sleep(10)
