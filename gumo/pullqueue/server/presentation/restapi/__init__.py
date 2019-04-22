from logging import getLogger
import flask.views

from gumo.core.injector import injector
from gumo.core import EntityKeyFactory
from gumo.pullqueue.server.application.enqueue import enqueue
from gumo.pullqueue.server.application.lease import LeaseTasksService
from gumo.pullqueue.server.application.lease import DeleteTasksService

logger = getLogger(__name__)
pullqueue_blueprint = flask.Blueprint('server', __name__)


class EnqueuePullTaskView(flask.views.MethodView):
    def get(self):
        task = enqueue(
            payload={'message': flask.request.args.get('message')},
            in_seconds=5
        )

        return flask.jsonify(task.to_json())


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
                task.to_json() for task in tasks
            ]
        })


class DeletePullTasksView(flask.views.MethodView):
    def delete(self, queue_name: str):
        key_factory = EntityKeyFactory()
        delete_service = injector.get(DeleteTasksService)  # type: DeleteTasksService

        body = flask.request.json  # type: dict
        if body is None or body.get('keys') == []:
            logger.debug(f'request body or keys is empty. delete processing is skipped.')
            return flask.jsonify({
                'processedTaskCount': 0,
            })

        keys = [
            key_factory.build_from_key_path(key_path=key_path)
            for key_path in body.get('keys', [])
        ]
        logger.debug(f'Delete Task Request: {len(keys)} items.')

        delete_service.delete_tasks(
            queue_name=queue_name,
            task_keys=keys,
        )

        return flask.jsonify({
            'processedTaskCount': len(keys),
        })


pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/enqueue',
    view_func=EnqueuePullTaskView.as_view(name='gumo/pullqueue/enqueue'),
    methods=['GET']
)

pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/<queue_name>/lease',
    view_func=LeasePullTasksView.as_view(name='gumo/pullqueue/lease'),
    methods=['GET']
)

pullqueue_blueprint.add_url_rule(
    '/gumo/pullqueue/<queue_name>/delete',
    view_func=DeletePullTasksView.as_view(name='gumo/pullqueue/delete'),
    methods=['DELETE']
)
