import sys
import logging
import datetime

import flask.views

from gumo.pullqueue.server import configure as pullqueue_configure
from gumo.pullqueue.server import pullqueue_flask_blueprint
from gumo.pullqueue.server import enqueue

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


pullqueue_configure(
    default_queue_name='pullqueue'
)

app = flask.Flask(__name__)
app.register_blueprint(pullqueue_flask_blueprint)


@app.route('/')
def hello():
    return 'Hi, gumo-pullqueue.'


@app.route('/enqueue')
def enqueue_handler():
    tag = flask.request.args.get('tag')

    task = enqueue(
        queue_name='pullqueue',
        payload={
            'message': 'this is message',
            'timestamp': datetime.datetime.utcnow().isoformat()
        },
        tag=tag,
    )

    return f'enqueue done. {task}'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
