import json
import datetime

from gumo.core.injector import injector
from gumo.pullqueue.server.infrastructure.mapper import DatastoreGumoPullTaskMapper
from gumo.datastore.infrastructure import DatastoreRepositoryMixin

from gumo.pullqueue.server.domain import GumoPullTask
from gumo.pullqueue import PullTask
from gumo.pullqueue.server.domain import PullTaskState

from gumo.core import EntityKeyFactory


def build_sample_pull_task():
    return GumoPullTask(
        task=PullTask(
            key=EntityKeyFactory().build_for_new(kind=GumoPullTask.KIND),
            queue_name='server',
            payload={'key': 'value'},
            schedule_time=datetime.datetime(2019, 1, 1)
        ),
        state=PullTaskState(),
        event_logs=[],
    )


def test_pull_task_mapper_to_datastore():
    mapper = injector.get(DatastoreGumoPullTaskMapper)  # type: DatastoreGumoPullTaskMapper
    pulltask = build_sample_pull_task()

    doc = mapper.to_datastore_entity(pulltask=pulltask)
    assert doc['payload'] == json.dumps({'key': 'value'})
    assert doc['schedule_time'] == pulltask.task.schedule_time
    assert doc['retry_count'] == pulltask.state.retry_count
    assert 'leased_by.address' not in doc


def test_pull_task_mapper_to_entity():
    mapper = injector.get(DatastoreGumoPullTaskMapper)  # type: DatastoreGumoPullTaskMapper
    pulltask = build_sample_pull_task()

    doc = mapper.to_datastore_entity(pulltask=pulltask)
    datastore_entity = DatastoreRepositoryMixin.DatastoreEntity(
        key=DatastoreRepositoryMixin().entity_key_mapper.to_datastore_key(entity_key=pulltask.key)
    )
    datastore_entity.update(doc)

    entity = mapper.to_entity(doc=datastore_entity)
    assert entity == pulltask
