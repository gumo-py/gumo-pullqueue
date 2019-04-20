import datetime
from typing import Optional

from gumo.core.injector import injector

from gumo.pullqueue.server.domain.configuration import PullQueueConfiguration
from gumo.pullqueue.server.application.enqueue.factory import GumoPullTaskFactory
from gumo.pullqueue.server.application.repository import GumoPullTaskRepository
from gumo.pullqueue import PullTask


def enqueue(
        payload: dict,
        schedule_time: Optional[datetime.datetime] = None,
        in_seconds: Optional[int] = None,
        queue_name: Optional[str] = None,
        tag: Optional[str] = None,
) -> PullTask:
    if queue_name is None:
        config = injector.get(PullQueueConfiguration)  # type: PullQueueConfiguration
        queue_name = config.default_queue_name

    pulltask = GumoPullTaskFactory().build(
        payload=payload,
        schedule_time=schedule_time,
        in_seconds=in_seconds,
        queue_name=queue_name,
        tag=tag,
    )

    repository = injector.get(GumoPullTaskRepository)  # type: GumoPullTaskRepository
    repository.save(pulltask=pulltask)

    return pulltask.task
