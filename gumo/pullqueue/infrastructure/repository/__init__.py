import datetime
from logging import getLogger
from typing import List
from injector import inject

from gumo.datastore.infrastructure import DatastoreRepositoryMixin
from gumo.pullqueue.application.repository import GumoPullTaskRepository
from gumo.pullqueue.domain import GumoPullTask
from gumo.pullqueue.domain import PullTaskStatus
from gumo.pullqueue.infrastructure.mapper import DatastoreGumoPullTaskMapper

logger = getLogger(__name__)


class DatastoreGumoPullTaskReqpository(GumoPullTaskRepository, DatastoreRepositoryMixin):
    @inject
    def __init__(
            self,
            pulltask_mapper: DatastoreGumoPullTaskMapper,
    ):
        super(DatastoreGumoPullTaskReqpository, self).__init__()
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
            size: int = 100,
    ) -> List[GumoPullTask]:
        now = datetime.datetime.utcnow().replace(microsecond=0)
        query = self.datastore_client.query(kind=GumoPullTask.KIND)
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
