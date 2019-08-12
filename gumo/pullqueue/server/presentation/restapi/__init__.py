from logging import getLogger
import flask.views

from gumo.core.injector import injector
from gumo.core import EntityKeyFactory
from gumo.pullqueue.server.domain import PullTaskWorker
from gumo.pullqueue.server.application.enqueue import enqueue
from gumo.pullqueue.server.application.lease import FetchAvailableTasksService
from gumo.pullqueue.server.application.lease import LeaseTaskService
from gumo.pullqueue.server.application.lease import LeaseExtendTaskService
from gumo.pullqueue.server.application.lease import FinalizeTaskService
from gumo.pullqueue.server.application.lease import FailureTaskService
from gumo.pullqueue.server.application.lease import CheckLeaseExpiredTasksService

logger = getLogger(__name__)
pullqueue_blueprint = flask.Blueprint('server', __name__)


class EnqueuePullTaskView(flask.views.MethodView):
    def get(self):
        task = enqueue(
            payload={'message': flask.request.args.get('message')},
            in_seconds=5
        )

        return flask.jsonify(task.to_json())


class CheckLeaseExpiredTaskView(flask.views.MethodView):
    def get(self):
        service: CheckLeaseExpiredTasksService = injector.get(CheckLeaseExpiredTasksService)

        tasks = service.check_and_update_expired_tasks()
        logger.info(f'Check lease expired task and update it, target task {len(tasks)} items.')

        return flask.jsonify({
            'tasks': [task.to_json() for task in tasks]
        })


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


class LeaseExtendPullTaskView(flask.views.MethodView):
    def post(self, queue_name: str):
        key_factory = EntityKeyFactory()
        service: LeaseExtendTaskService = injector.get(LeaseExtendTaskService)

        payload: dict = flask.request.json
        if payload.get('key') is None:
            raise ValueError(f'Invalid request payload: missing `key`')

        key = key_factory.build_from_key_path(key_path=payload.get('key'))
        lease_extend_time = payload.get('lease_extend_time', 300)
        worker_name = payload.get('worker_name', '<unknown>')

        worker = PullTaskWorker(
            address=flask.request.headers.get('X-Appengine-User-Ip', flask.request.remote_addr),
            name=worker_name,
        )

        task = service.lease_extend_task(
            queue_name=queue_name,
            key=key,
            lease_extend_time=lease_extend_time,
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


class FailurePullTaskView(flask.views.MethodView):
    def post(self, queue_name: str):
        key_factory = EntityKeyFactory()
        service: FailureTaskService = injector.get(FailureTaskService)

        payload: dict = flask.request.json
        if payload.get('key') is None:
            raise ValueError(f'Invalid request payload: missing `key`')

        key = key_factory.build_from_key_path(key_path=payload.get('key'))
        worker_name = payload.get('worker_name', '<unknown>')
        message = payload.get('message')

        worker = PullTaskWorker(
            address=flask.request.headers.get('X-Appengine-User-Ip', flask.request.remote_addr),
            name=worker_name,
        )

        task = service.failure_task(
            queue_name=queue_name,
            key=key,
            message=message,
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
    '/gumo/pullqueue/check_expired_tasks',
    view_func=CheckLeaseExpiredTaskView.as_view(name='gumo/pullqueue/check_expired_tasks'),
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
    '/gumo/pullqueue/<queue_name>/lease_extend',
    view_func=LeaseExtendPullTaskView.as_view(name='gumo/pullqueue/lease_extend'),
    methods=['POST']
)

pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/<queue_name>/finalize',
    view_func=FinalizePullTaskView.as_view(name='gumo/pullqueue/finalize'),
    methods=['POST']
)

pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/<queue_name>/failure',
    view_func=FailurePullTaskView.as_view(name='gumo/pullqueue/failure'),
    methods=['POST']
)
