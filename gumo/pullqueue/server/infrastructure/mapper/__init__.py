import json
import datetime

from gumo.datastore.infrastructure import DatastoreMapperMixin
from gumo.datastore.infrastructure import DatastoreEntity

from gumo.pullqueue.server.domain import GumoPullTask
from gumo.pullqueue.domain import PullTask
from gumo.pullqueue.server.domain import PullTaskState
from gumo.pullqueue.server.domain import PullTaskWorker
from gumo.pullqueue.server.domain import PullTaskStatus
from gumo.pullqueue.server.domain import TaskEvent


class DatastoreGumoPullTaskMapper(DatastoreMapperMixin):
    DEFAULT_LEASE_EXPIRES_AT = datetime.datetime(2000, 1, 1)

    def to_datastore_entity(self, pulltask: GumoPullTask) -> DatastoreEntity:
        datastore_key = self.entity_key_mapper.to_datastore_key(entity_key=pulltask.key)
        j = DatastoreEntity(key=datastore_key, exclude_from_indexes=['event_logs'])
        j.update({
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
        })

        if pulltask.state.lease_expires_at:
            j['lease_expires_at'] = pulltask.state.lease_expires_at
        else:
            j['lease_expires_at'] = self.DEFAULT_LEASE_EXPIRES_AT

        if pulltask.state.leased_by:
            j.update({
                'leased_by.address': pulltask.state.leased_by.address,
                'leased_by.name': pulltask.state.leased_by.name,
            })

        j['event_logs'] = json.dumps([
            event.to_json() for event in pulltask.event_logs
        ], ensure_ascii=False, indent=4)

        return j

    def to_entity(self, doc: DatastoreEntity) -> GumoPullTask:
        key = self.entity_key_mapper.to_entity_key(datastore_key=doc.key)

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

        event_logs = []
        if doc.get('event_logs') is not None:
            for event_payload in json.loads(doc.get('event_logs')):
                event_logs.append(TaskEvent.from_json(event_payload))

        return GumoPullTask(
            task=task,
            state=state,
            event_logs=event_logs,
        )
