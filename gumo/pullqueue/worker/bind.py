from gumo.pullqueue.worker.application.repository import PullTaskRemoteRepository
from gumo.pullqueue.worker.infrastructure.repository import HttpRequestPullTaskRepository


def pullqueue_worker_bind(binder):
    binder.bind(PullTaskRemoteRepository, to=HttpRequestPullTaskRepository)
