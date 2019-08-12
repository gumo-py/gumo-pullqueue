from logging import getLogger
import flask.views

from gumo.core.injector import injector
from gumo.core import EntityKeyFactory
from gumo.pullqueue.server.domain import PullTaskWorker
from gumo.pullqueue.server.application.enqueue import enqueue
from gumo.pullqueue.server.application.lease import FetchAvailableTasksService
from gumo.pullqueue.server.application.lease import LeaseTaskService
from gumo.pullqueue.server.application.lease import FinalizeTaskService

logger = getLogger(__name__)
pullqueue_blueprint = flask.Blueprint('server', __name__)


class EnqueuePullTaskView(flask.views.MethodView):
    def get(self):
        task = enqueue(
            payload={'message': flask.request.args.get('message')},
            in_seconds=5
        )

        return flask.jsonify(task.to_json())


class AvailablePullTasksView(flask.views.MethodView):
    def get(self, queue_name: str):
        service: FetchAvailableTasksService = injector.get(FetchAvailableTasksService)
        tasks = service.fetch_tasks(
            queue_name=queue_name,
            lease_size=int(flask.request.args.get('lease_size', '10')),
            tag=flask.request.args.get('tag'),
        )

        return flask.jsonify({
            'tasks': [
                task.to_json() for task in tasks
            ]
        })


class LeasePullTaskView(flask.views.MethodView):
    def post(self, queue_name: str):
        key_factory = EntityKeyFactory()
        lease_service: LeaseTaskService = injector.get(LeaseTaskService)

        payload: dict = flask.request.json
        if payload.get('key') is None:
            raise ValueError(f'Invalid request payload: missing `key`')

        key = key_factory.build_from_key_path(key_path=payload.get('key'))
        lease_time = payload.get('lease_time', 300)
        worker_name = payload.get('worker_name', '<unknown>')

        worker = PullTaskWorker(
            address=flask.request.headers.get('X-Appengine-User-Ip', flask.request.remote_addr),
            name=worker_name,
        )

        task = lease_service.lease_task(
            queue_name=queue_name,
            key=key,
            lease_time=lease_time,
            worker=worker,
        )

        return flask.jsonify({'task': task.to_json()})


class FinalizePullTaskView(flask.views.MethodView):
    def post(self, queue_name: str):
        key_factory = EntityKeyFactory()
        service: FinalizeTaskService = injector.get(FinalizeTaskService)

        payload: dict = flask.request.json
        if payload.get('key') is None:
            raise ValueError(f'Invalid request payload: missing `key`')

        key = key_factory.build_from_key_path(key_path=payload.get('key'))
        worker_name = payload.get('worker_name', '<unknown>')

        worker = PullTaskWorker(
            address=flask.request.headers.get('X-Appengine-User-Ip', flask.request.remote_addr),
            name=worker_name,
        )

        task = service.finalize_task(
            queue_name=queue_name,
            key=key,
            worker=worker,
        )

        return flask.jsonify({
            'task': task.to_json()
        })


pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/enqueue',
    view_func=EnqueuePullTaskView.as_view(name='gumo/pullqueue/enqueue'),
    methods=['GET']
)

pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/<queue_name>/tasks/available',
    view_func=AvailablePullTasksView.as_view(name='gumo/pullqueue/tasks/available'),
    methods=['GET']
)

pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/<queue_name>/lease',
    view_func=LeasePullTaskView.as_view(name='gumo/pullqueue/lease'),
    methods=['POST']
)

pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/<queue_name>/finalize',
    view_func=FinalizePullTaskView.as_view(name='gumo/pullqueue/finalize'),
    methods=['POST']
)
