from logging import getLogger
import flask.views

from gumo.core.injector import injector
from gumo.pullqueue.server.application.enqueue import enqueue
from gumo.pullqueue.server.application.lease import LeaseTasksService
from gumo.pullqueue.server.application.encoder import PullTaskJSONEncoder


logger = getLogger(__name__)
pullqueue_blueprint = flask.Blueprint('server', __name__)


class EnqueuePullTaskView(flask.views.MethodView):
    def get(self):
        task = enqueue(
            payload={'message': flask.request.args.get('message')},
            in_seconds=5
        )

        return flask.jsonify(
            PullTaskJSONEncoder(pulltask=task).to_json()
        )


class LeasePullTasksView(flask.views.MethodView):
    def get(self, queue_name: str):
        lease_service = injector.get(LeaseTasksService)  # type: LeaseTasksService
        tasks = lease_service.lease_tasks(
            queue_name=queue_name,
            lease_time=3600,
            lease_size=100,
        )

        return flask.jsonify({
            'tasks': [
                PullTaskJSONEncoder(pulltask=task).to_json()
                for task in tasks
            ]
        })



pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/enqueue',
    view_func=EnqueuePullTaskView.as_view(name='gumo/server/enqueue'),
    methods=['GET']
)

pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/<queue_name>/lease',
    view_func=LeasePullTasksView.as_view(name='gumo/pullqueue/lease'),
    methods=['GET']
)
