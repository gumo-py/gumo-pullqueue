import os

from gumo.core import configure as core_configure
from gumo.datastore import configure as datastore_configure
from gumo.pullqueue import configure as pullqueue_configure
from gumo.pullqueue_worker import configure as pullqueue_worker_configure

if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') is None:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/credential.json'


if 'DATASTORE_EMULATOR_HOST' not in os.environ:
    raise RuntimeError('Tests must be present DATASTORE_EMULATOR_HOST environment variables.')

core_configure(
    google_cloud_project='gumo-pullqueue',
    google_cloud_location='asia-northeast1',
)

datastore_configure(
    use_local_emulator='DATASTORE_EMULATOR_HOST' in os.environ,
    emulator_host=os.environ.get('DATASTORE_EMULATOR_HOST'),
    namespace=os.environ.get('DATASTORE_NAMESPACE'),
)

pullqueue_configure(
    default_queue_name='pullqueue'
)

pullqueue_worker_configure(
    server_url='http://server:8080',
    polling_sleep_seconds=0,
)
