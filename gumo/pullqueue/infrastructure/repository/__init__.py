from logging import getLogger

from injector import inject

from gumo.datastore.infrastructure import DatastoreRepositoryMixin
from gumo.pullqueue.application.repository import GumoPullTaskRepository
from gumo.pullqueue.domain import GumoPullTask
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
