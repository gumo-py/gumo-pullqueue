from logging import getLogger

from gumo.pullqueue.server.domain import PullTask

logger = getLogger(__name__)


class PullTaskJSONEncoder:
    def __init__(self, pulltask: PullTask):
        self._task = pulltask

    def to_json(self) -> dict:
        return {
            'key': self._task.key.key_path(),
            'payload': self._task.payload,
            'schedule_time': self._task.schedule_time.isoformat(),
            'created_at': self._task.created_at.isoformat(),
            'queue_name': self._task.queue_name,
            'tag': self._task.tag,
        }
