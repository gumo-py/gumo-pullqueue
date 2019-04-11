import json

from injector import inject

from gumo.core import EntityKey
from gumo.datastore.infrastructure import EntityKeyMapper
from gumo.pullqueue.domain import GumoPullTask
from gumo.pullqueue.domain import PullTask
from gumo.pullqueue.domain import PullTaskState
from gumo.pullqueue.domain import PullTaskWorker


class DatastoreGumoPullTaskMapper:
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

            # pulltask.state
            'execution_count': pulltask.state.execution_count,
            'retry_count': pulltask.state.retry_count,
            'last_executed_at': pulltask.state.last_executed_at,
            'next_executed_at': pulltask.state.next_executed_at,
            'leased_at': pulltask.state.leased_at,
            'lease_expires_at': pulltask.state.lease_expires_at,
        }

        if pulltask.state.leased_by:
            j.update({
                'leased_by.address': pulltask.state.leased_by.address,
                'leased_by.name': pulltask.state.leased_by.name,
            })

        return j

    def to_entity(self, key: EntityKey, doc: dict) -> GumoPullTask:
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

        state = PullTaskState(
            execution_count=doc.get('execution_count'),
            retry_count=doc.get('retry_count'),
            last_executed_at=doc.get('last_executed_at'),
            next_executed_at=doc.get('next_executed_at'),
            leased_at=doc.get('leased_at'),
            lease_expires_at=doc.get('lease_expires_at'),
            leased_by=leased_by
        )

        # TODO: implements log mapping rule.
        logs = []

        return GumoPullTask(
            task=task,
            state=state,
            logs=logs,
        )
