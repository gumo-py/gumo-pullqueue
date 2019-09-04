import os
import sys
import logging

from gumo.core.injector import injector
from gumo.pullqueue.worker import configure as pullqueue_worker_configure
from gumo.pullqueue.worker.application.service import FetchAvailableTasksService
from gumo.pullqueue.worker.application.service import LeaseTaskService
from gumo.pullqueue.worker.application.service import FinalizeTaskService

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

if 'GAE_DEPLOYMENT_ID' not in os.environ and os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') is None:
    raise RuntimeError('environment variable "GOOGLE_APPLICATION_CREDENTIALS" must be present.')

pullqueue_worker_configure(
    server_url=os.environ.get('SERVER_URL', 'https://gumo-pullqueue.appspot.com/'),
    target_audience_client_id=os.environ.get(
        'AUDIENCE_CLIENT_ID',
        '662327322493-6h9aduu73vuusvietthatbvngdp28hnv.apps.googleusercontent.com'
    ),
)

if __name__ == '__main__':
    import time

    QUEUE_NAME = 'pullqueue'

    fetch_service: FetchAvailableTasksService = injector.get(FetchAvailableTasksService)
    lease_service: LeaseTaskService = injector.get(LeaseTaskService)
    finalize_service: FinalizeTaskService = injector.get(FinalizeTaskService)

    while True:
        available_tasks = fetch_service.available_tasks(
            queue_name=QUEUE_NAME,
            lease_size=1,
        )

        if len(available_tasks) == 0:
            print('available tasks are not found.')
            print('sleep 5 seconds ...')
            time.sleep(5)
            continue

        leased_task = lease_service.lease_task(
            queue_name=QUEUE_NAME,
            task=available_tasks[0],
            lease_time=30,
        )

        print(f'leased_task = {leased_task}')
        print('sleep 5 seconds ...')
        time.sleep(5)
        finalize_service.finalize_task(task=leased_task)
        print('finalized.')

        print('sleep 10 seconds...')
        time.sleep(10)
