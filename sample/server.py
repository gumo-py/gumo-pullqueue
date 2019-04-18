import os
import sys
import logging

import flask.views

from gumo.core import MockAppEngineEnvironment
from gumo.core import configure as core_configure
from gumo.datastore import configure as datastore_configure
from gumo.pullqueue.server import configure as pullqueue_configure
from gumo.pullqueue.server.presentation.restapi import pullqueue_blueprint

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

# Application framework initialization process.
core_configure(
    google_cloud_project=os.environ.get('PROJECT_NAME'),
    google_cloud_location=os.environ.get('PROJECT_LOCATION'),
)

datastore_configure(
    use_local_emulator='DATASTORE_EMULATOR_HOST' in os.environ,
    emulator_host=os.environ.get('DATASTORE_EMULATOR_HOST'),
    namespace=os.environ.get('DATASTORE_NAMESPACE'),
)

pullqueue_configure(
    default_queue_name='pullqueue'
)

app = flask.Flask(__name__)
app.register_blueprint(pullqueue_blueprint)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
