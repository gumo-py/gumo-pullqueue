import os
import sys
import logging

from gumo.core import MockAppEngineEnvironment
from gumo.pullqueue_worker import configure as pullqueue_worker_configure


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
