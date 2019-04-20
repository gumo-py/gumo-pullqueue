import dataclasses
import datetime
from typing import Optional

from gumo.core import EntityKey
from gumo.core import EntityKeyFactory


@dataclasses.dataclass(frozen=True)
class PullTask:
    """
    Task payload to process at enqueue time and lease time
    """
    key: EntityKey
    queue_name: str
    payload: Optional[dict] = dataclasses.field(default_factory=dict)
    schedule_time: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.utcnow)
    created_at: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.utcnow)
    tag: Optional[str] = None

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.key == other.key

    def to_json(self) -> dict:
        return _PullTaskJSONEncoder(pulltask=self).to_json()

    @classmethod
    def from_json(cls, doc: dict):
        """
        :param doc: Dictionary of PullTask
        :type doc: dict
        :rtype: PullTask
        """
        return _PullTaskJSONDecoder(doc=doc).decode()


class _PullTaskJSONEncoder:
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


class _PullTaskJSONDecoder:
    def __init__(self, doc: dict):
        self._doc = doc

        if not isinstance(doc, dict):
            raise ValueError(f'doc must be an instance of dict, but received type {type(doc)} (value is {doc})')

    def decode(self) -> PullTask:
        return PullTask(
            key=EntityKeyFactory().build_from_key_path(key_path=self._doc.get('key')),
            payload=self._doc.get('payload'),
            schedule_time=datetime.datetime.fromisoformat(self._doc.get('schedule_time')),
            created_at=datetime.datetime.fromisoformat(self._doc.get('created_at')),
            queue_name=self._doc.get('queue_name'),
            tag=self._doc.get('tag'),
        )
