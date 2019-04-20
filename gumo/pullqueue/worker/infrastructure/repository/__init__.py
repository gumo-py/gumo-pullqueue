import requests
import datetime
import json
from logging import getLogger
from urllib.parse import urljoin
from typing import List
from typing import Optional
from typing import Union

from gumo.core import EntityKeyFactory
from gumo.core import EntityKey
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

    def _requests(
            self,
            method: str,
            path: str,
            payload: Optional[dict] = None,
    ) -> Union[dict, str]:
        url = urljoin(
            base=self._server_url(),
            url=path,
        )

        data = None
        if payload is not None:
            data = json.dumps(payload)

        response = requests.request(
            method=method,
            url=url,
            data=data,
            headers={
                'Content-Type': 'application/json',
            }
        )

        if response.headers.get('Content-Type') == 'application/json':
            return response.json()
        else:
            return response.content

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

    def delete_tasks(
            self,
            queue_name: str,
            keys: List[EntityKey],
    ):
        payload = {
            'keys': [key.key_path() for key in keys]

        }
        logger.debug(f'payload = {payload}')

        return self._requests(
            method='DELETE',
            path=f'/gumo/pullqueue/{queue_name}/delete',
            payload=payload,
        )
