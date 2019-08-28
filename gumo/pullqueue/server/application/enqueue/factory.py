import datetime
from typing import Optional

from gumo.pullqueue import PullTask
from gumo.pullqueue.server.domain import GumoPullTask
from gumo.pullqueue.server.domain import EnqueueRequest
from gumo.pullqueue.server.domain import PullTaskWorker

from gumo.datastore import EntityKeyFactory


class GumoPullTaskFactory:
    def build(
            self,
            payload: dict,
            schedule_time: Optional[datetime.datetime] = None,
            in_seconds: Optional[int] = None,
            queue_name: Optional[str] = None,
            tag: Optional[str] = None,
    ) -> GumoPullTask:

        now = datetime.datetime.utcnow().replace(microsecond=0)

        if schedule_time is not None and in_seconds is not None:
            raise ValueError('schedule_time and in_seconds should be specified exclusively.')

        if in_seconds:
            delta = datetime.timedelta(seconds=in_seconds)
            schedule_time = now + delta

        if schedule_time is None:
            schedule_time = now

        pull_task = PullTask(
            key=EntityKeyFactory().build_for_new(
                kind=GumoPullTask.KIND,
            ),
            payload=payload,
            schedule_time=schedule_time,
            created_at=now,
            queue_name=queue_name,
            tag=tag,
        )

        event = EnqueueRequest(
            event_at=now,
            worker=PullTaskWorker.get_server()
        )
        task = event.build_next(pulltask=pull_task)

        return task
