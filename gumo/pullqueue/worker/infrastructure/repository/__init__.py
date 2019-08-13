import json
import uuid
import requests
from logging import getLogger
from urllib.parse import urljoin
from typing import List
from typing import Optional
from typing import Union

from gumo.core import EntityKey
from gumo.core import get_google_id_token_credentials

from gumo.pullqueue import PullTask
from gumo.pullqueue.worker.application.repository import PullTaskRemoteRepository

logger = getLogger(__name__)


class HttpRequestPullTaskRepository(PullTaskRemoteRepository):
    @property
    def _worker_name(self):
        return self._configuration.worker_name

    @property
    def _request_log_enabled(self):
        return self._configuration.request_logger is not None

    @property
    def _logger(self):
        return self._configuration.request_logger

    def _log_request(self, request_id, method, url, data, headers):
        if not self._request_log_enabled:
            return

        self._logger.debug(
            f'[HttpRequestPullTaskRepo] request_id={request_id} {method} {url} (data={data}, headers={headers})'
        )

    def _log_response(self, request_id, response):
        if not self._request_log_enabled:
            return

        self._logger.debug(
            f'[HttpRequestPullTaskRepo] request_id={request_id} {response}'
        )

    def _server_url(self) -> str:
        return self._configuration.server_url

    def _audience_client_id(self) -> Optional[str]:
        return self._configuration.target_audience_client_id

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

        request_id = str(uuid.uuid4())
        headers = {
            'Content-Type': 'application/json',
            'X-Worker-Request-ID': request_id,
        }

        if self._request_log_enabled:
            self._log_request(
                request_id=request_id,
                method=method,
                url=url,
                data=data,
                headers=headers
            )

        if self._audience_client_id():
            id_token_credential, request = get_google_id_token_credentials(
                target_audience=self._audience_client_id(),
                with_refresh=True
            )
            id_token_credential.apply(headers=headers)

        response = requests.request(
            method=method,
            url=url,
            data=data,
            headers=headers
        )

        if self._request_log_enabled:
            self._log_response(
                request_id=request_id,
                response=response,
            )

        if response.headers.get('Content-Type') == 'application/json':
            return response.json()
        else:
            return response.content

    def available_tasks(
            self,
            queue_name: str,
            size: int = 10,
            tag: Optional[str] = None,
    ) -> List[PullTask]:
        params = [
            f'lease_size={size}',
        ]
        if tag is not None:
            params.append(f'tag={tag}')
        query_string = '&'.join(params)

        plain_tasks = self._requests(
            method='GET',
            path=f'/gumo/pullqueue/{queue_name}/tasks/available?{query_string}',
        )

        return [PullTask.from_json(j) for j in plain_tasks.get('tasks')]

    def lease_task(
            self,
            queue_name: str,
            task: PullTask,
            lease_time: int = 300,
    ) -> PullTask:
        leased_plain_task = self._requests(
            method='POST',
            path=f'/gumo/pullqueue/{queue_name}/lease',
            payload={
                'key': task.key.key_path(),
                'lease_time': lease_time,
                'worker_name': self._worker_name,
            }
        )

        task = PullTask.from_json(doc=leased_plain_task.get('task'))
        return task

    def finalize_task(
            self,
            queue_name: str,
            key: EntityKey,
    ) -> PullTask:
        payload = {
            'key': key.key_path(),
            'worker_name': self._worker_name,
        }
        logger.debug(f'payload = {payload}')

        response = self._requests(
            method='POST',
            path=f'/gumo/pullqueue/{queue_name}/finalize',
            payload=payload,
        )

        task = PullTask.from_json(doc=response.get('task'))
        return task

    def failure_task(
            self,
            queue_name: str,
            key: EntityKey,
            message: str,
    ) -> PullTask:
        payload = {
            'key': key.key_path(),
            'message': message,
            'worker_name': self._worker_name,
        }

        response = self._requests(
            method='POST',
            path=f'/gumo/pullqueue/{queue_name}/failure',
            payload=payload,
        )

        task = PullTask.from_json(doc=response.get('task'))
        return task

    def lease_extend_task(
            self,
            queue_name: str,
            key: EntityKey,
            lease_extend_time: int,
    ) -> PullTask:
        payload = {
            'key': key.key_path(),
            'lease_extend_time': lease_extend_time,
            'worker_name': self._worker_name,
        }

        response = self._requests(
            method='POST',
            path=f'/gumo/pullqueue/{queue_name}/lease_extend',
            payload=payload,
        )
        task = PullTask.from_json(doc=response.get('task'))
        return task
