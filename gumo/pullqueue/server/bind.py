from gumo.pullqueue.server.application.repository import GumoPullTaskRepository
from gumo.pullqueue.server.infrastructure.repository import DatastoreGumoPullTaskReqpository


def pullqueue_bind(binder):
    binder.bind(GumoPullTaskRepository, to=DatastoreGumoPullTaskReqpository)
