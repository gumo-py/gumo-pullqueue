import requests
import datetime
from logging import getLogger
from urllib.parse import urljoin
from typing import List

from gumo.core import EntityKeyFactory
from gumo.pullqueue import PullTask
from gumo.pullqueue.worker.application.repository import PullTaskRemoteRepository

logger = getLogger(__name__)


class PullTaskJSONDecoder:
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


class HttpRequestPullTaskRepository(PullTaskRemoteRepository):
    def _server_url(self) -> str:
        return self._configuration.server_url

    def _requests(self, method, path) -> dict:
        url = urljoin(
            base=self._server_url(),
            url=path,
        )
        response = requests.request(method=method, url=url)
        return response.json()

    def lease_tasks(
            self,
            queue_name: str,
            size: int = 100,
    ) -> List[PullTask]:
        plain_tasks = self._requests(
            method='GET',
            path=f'/gumo/pullqueue/{queue_name}/lease'
        )

        tasks = [
            PullTaskJSONDecoder(doc=doc).decode() for doc in plain_tasks.get('tasks', [])
        ]

        return tasks
