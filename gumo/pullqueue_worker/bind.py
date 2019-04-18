from gumo.pullqueue_worker.application.repository import PullTaskRemoteRepository
from gumo.pullqueue_worker.infrastructure.repository import HttpRequestPullTaskRepository


def pullqueue_worker_bind(binder):
    binder.bind(PullTaskRemoteRepository, to=HttpRequestPullTaskRepository)
