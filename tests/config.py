from gumo.pullqueue.server import configure as pullqueue_configure
from gumo.pullqueue.worker import configure as pullqueue_worker_configure


pullqueue_configure(
    default_queue_name='server'
)

pullqueue_worker_configure(
    server_url='http://server:8080',
    polling_sleep_seconds=0,
)
