import requests
import json
from logging import getLogger
from urllib.parse import urljoin
from typing import List
from typing import Optional
from typing import Union

from gumo.core import EntityKey
from gumo.pullqueue import PullTask
from gumo.pullqueue.worker.application.repository import PullTaskRemoteRepository

logger = getLogger(__name__)


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
            PullTask.from_json(doc=doc) for doc in plain_tasks.get('tasks', [])
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
