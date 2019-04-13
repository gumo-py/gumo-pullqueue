from logging import getLogger
import flask.views

from gumo.core.injector import injector
from gumo.pullqueue.application.enqueue import enqueue
from gumo.pullqueue.application.lease import LeaseTasksService


logger = getLogger(__name__)
pullqueue_blueprint = flask.Blueprint('pullqueue', __name__)


class EnqueuePullTaskView(flask.views.MethodView):
    def get(self):
        task = enqueue(
            payload={'message': flask.request.args.get('message')},
            in_seconds=5
        )

        return str(task)


class LeasePullTasksView(flask.views.MethodView):
    def get(self):
        logger.info('call lease')
        lease_service = injector.get(LeaseTasksService)  # type: LeaseTasksService
        tasks = lease_service.lease_tasks(
            lease_time=3600,
            lease_size=100,
        )

        return str(tasks)


pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/enqueue',
    view_func=EnqueuePullTaskView.as_view(name='gumo/pullqueue/enqueue'),
    methods=['GET']
)

pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/lease',
    view_func=LeasePullTasksView.as_view(name='gumo/pulllqueue/lease'),
    methods=['GET']
)
