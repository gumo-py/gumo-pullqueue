import datetime
from logging import getLogger
from typing import List
from typing import Optional
from injector import inject

from gumo.core import EntityKey
from gumo.datastore.infrastructure import DatastoreRepositoryMixin
from gumo.pullqueue.server.application.repository import GumoPullTaskRepository
from gumo.pullqueue.server.domain import GumoPullTask
from gumo.pullqueue.server.domain import PullTaskStatus
from gumo.pullqueue.server.domain.configuration import PullQueueConfiguration
from gumo.pullqueue.server.infrastructure.mapper import DatastoreGumoPullTaskMapper

logger = getLogger(__name__)


class DatastoreGumoPullTaskReqpository(GumoPullTaskRepository, DatastoreRepositoryMixin):
    @inject
    def __init__(
            self,
            pullqueue_configuration: PullQueueConfiguration,
            pulltask_mapper: DatastoreGumoPullTaskMapper,
    ):
        self._pullqueue_configuration = pullqueue_configuration
        self._pulltask_mapper = pulltask_mapper

    def save(
            self,
            pulltask: GumoPullTask
    ):
        datastore_key = self.entity_key_mapper.to_datastore_key(entity_key=pulltask.key)
        datastore_entity = self.DatastoreEntity(key=datastore_key)
        datastore_entity.update(self._pulltask_mapper.to_datastore_entity(pulltask=pulltask))
        self.datastore_client.put(datastore_entity)

    def fetch_available_tasks(
            self,
            queue_name: str,
            size: int = 100,
            now: Optional[datetime.datetime] = None,
    ) -> List[GumoPullTask]:
        now = now if now else datetime.datetime.utcnow().replace(microsecond=0)

        query = self.datastore_client.query(kind=GumoPullTask.KIND)
        query.add_filter('queue_name', '=', queue_name)
        query.add_filter('status_name', '=', PullTaskStatus.initial.name)
        query.add_filter('schedule_time', '<=', now)
        query.order = ['schedule_time']

        tasks = []
        for datastore_entity in query.fetch(limit=size):
            task = self._pulltask_mapper.to_entity(doc=datastore_entity)
            tasks.append(task)

        return tasks

    def total_count(self) -> int:
        query = self.datastore_client.query(kind=GumoPullTask.KIND)
        query.keys_only()
        return len(list(query.fetch()))

    def purge(self):
        query = self.datastore_client.query(kind=GumoPullTask.KIND)
        query.keys_only()
        keys = [doc.key for doc in query.fetch()]
        self.datastore_client.delete_multi(keys)

    def fetch_keys(self, keys: List[EntityKey]) -> List[GumoPullTask]:
        datastore_keys = [
            self.entity_key_mapper.to_datastore_key(entity_key=key) for key in keys
        ]
        datastore_entities = self.datastore_client.get_multi(keys=datastore_keys)

        entities = [
            self._pulltask_mapper.to_entity(doc=doc) for doc in datastore_entities
        ]
        return entities

    def put_multi(self, tasks: List[GumoPullTask]):
        datastore_entities = []
        for pulltask in tasks:
            datastore_key = self.entity_key_mapper.to_datastore_key(entity_key=pulltask.key)
            datastore_entity = self.DatastoreEntity(key=datastore_key)
            datastore_entity.update(
                self._pulltask_mapper.to_datastore_entity(pulltask=pulltask)
            )
            datastore_entities.append(datastore_entity)

        self.datastore_client.put_multi(datastore_entities)
