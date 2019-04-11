from gumo.pullqueue.application.repository import GumoPullTaskRepository
from gumo.pullqueue.infrastructure.repository import DatastoreGumoPullTaskReqpository


def pullqueue_bind(binder):
    binder.bind(GumoPullTaskRepository, to=DatastoreGumoPullTaskReqpository)
