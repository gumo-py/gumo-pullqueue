import json
import uuid
import requests
from logging import getLogger
from urllib.parse import urljoin
from typing import List
from typing import Optional
from typing import Union

import google.oauth2.service_account
import google.auth.transport.requests

from gumo.core import EntityKey
from gumo.core import get_google_oauth_credential
from gumo.core import get_google_id_token_credential

from gumo.pullqueue import PullTask
from gumo.pullqueue.worker.application.repository import PullTaskRemoteRepository

logger = getLogger(__name__)


def _get_iap_header(audience_client_id: str):
    oauth_token_uri = 'https://www.googleapis.com/oauth2/v4/token'

    signer = get_google_oauth_credential()
    service_account_credentials = google.oauth2.service_account.Credentials(
        signer.signer,
        signer.signer_email,
        token_uri=oauth_token_uri,
        additional_claims={
            'target_audience': audience_client_id,
        }
    )

    request = google.auth.transport.requests.Request()
    body = {
        'assertion': service_account_credentials._make_authorization_grant_assertion(),
        'grant_type': google.oauth2._client._JWT_GRANT_TYPE,
    }
    token_response = google.oauth2._client._token_endpoint_request(request, oauth_token_uri, body)

    return 'Bearer ' + token_response['id_token']


class HttpRequestPullTaskRepository(PullTaskRemoteRepository):
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

    def _authorization_header(self) -> Optional[str]:
        if self._audience_client_id() is None:
            return

        return _get_iap_header(
            audience_client_id=self._configuration.target_audience_client_id,
        )

    def _requests(
            self,
            method: str,
            path: str,
            payload: Optional[dict] = None,
    ) -> Union[dict, str]:
        id_token_credential, request = get_google_id_token_credential(
            target_audience=self._configuration.target_audience_client_id,
            with_refresh=True
        )
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
