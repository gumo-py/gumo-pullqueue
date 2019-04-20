import json
import datetime

from injector import inject

from gumo.datastore.infrastructure import EntityKeyMapper
from gumo.pullqueue.server.domain import GumoPullTask
from gumo.pullqueue.domain import PullTask
from gumo.pullqueue.server.domain import PullTaskState
from gumo.pullqueue.server.domain import PullTaskWorker
from gumo.pullqueue.server.domain import PullTaskStatus


class DatastoreGumoPullTaskMapper:
    DEFAULT_LEASE_EXPIRES_AT = datetime.datetime(2000, 1, 1)

    @inject
    def __init__(
            self,
            entity_key_mapper: EntityKeyMapper
    ):
        self._entity_key_mapper = entity_key_mapper

    def to_datastore_entity(self, pulltask: GumoPullTask) -> dict:
        j = {
            # pulltask.task
            'payload': json.dumps(pulltask.task.payload),
            'schedule_time': pulltask.task.schedule_time,
            'created_at': pulltask.task.created_at,
            'queue_name': pulltask.task.queue_name,
            'tag': pulltask.task.tag,

            # pulltask.status
            'status_name': pulltask.state.status.name,
            'execution_count': pulltask.state.execution_count,
            'retry_count': pulltask.state.retry_count,
            'last_executed_at': pulltask.state.last_executed_at,
            'next_executed_at': pulltask.state.next_executed_at,
            'leased_at': pulltask.state.leased_at,
        }

        if pulltask.state.lease_expires_at:
            j['lease_expires_at'] = pulltask.state.lease_expires_at
        else:
            j['lease_expires_at'] = self.DEFAULT_LEASE_EXPIRES_AT

        if pulltask.state.leased_by:
            j.update({
                'leased_by.address': pulltask.state.leased_by.address,
                'leased_by.name': pulltask.state.leased_by.name,
            })

        return j

    def to_entity(self, doc: dict) -> GumoPullTask:
        key = self._entity_key_mapper.to_entity_key(datastore_key=doc.key)

        task = PullTask(
            key=key,
            payload=json.loads(doc.get('payload')),
            schedule_time=doc.get('schedule_time'),
            created_at=doc.get('created_at'),
            queue_name=doc.get('queue_name'),
            tag=doc.get('tag'),
        )

        if doc.get('leased_by.address'):
            leased_by = PullTaskWorker(
                address=doc.get('leased_by.address'),
                name=doc.get('leased_by.name'),
            )
        else:
            leased_by = None

        if doc.get('lease_expires_at') == self.DEFAULT_LEASE_EXPIRES_AT:
            lease_expires_at = None
        else:
            lease_expires_at = doc.get('lease_expires_at')

        state = PullTaskState(
            status=PullTaskStatus.get(doc.get('status_name')),
            execution_count=doc.get('execution_count'),
            retry_count=doc.get('retry_count'),
            last_executed_at=doc.get('last_executed_at'),
            next_executed_at=doc.get('next_executed_at'),
            leased_at=doc.get('leased_at'),
            lease_expires_at=lease_expires_at,
            leased_by=leased_by
        )

        # TODO: implements log mapping rule.
        logs = []

        return GumoPullTask(
            task=task,
            state=state,
            logs=logs,
        )
