from injector import singleton

from logging import getLogger

from typing import Optional

from gumo.core.injector import injector
from gumo.pullqueue.worker.domain.configuration import PullQueueWorkerConfiguration
from gumo.pullqueue.worker.bind import pullqueue_worker_bind

logger = getLogger(__name__)


class _ConfigurationFactory:
    DEFAULT_POLLING_SLEEP_SECONDS = 10

    def build(
            self,
            server_url: str,
            polling_sleep_seconds: Optional[int] = None,
            request_logger: Optional[object] = None,
            target_audience_client_id: Optional[str] = None,
    ) -> PullQueueWorkerConfiguration:

        if polling_sleep_seconds is None:
            polling_sleep_seconds = self.DEFAULT_POLLING_SLEEP_SECONDS

        return PullQueueWorkerConfiguration(
            server_url=server_url,
            polling_sleep_seconds=polling_sleep_seconds,
            request_logger=request_logger,
            target_audience_client_id=target_audience_client_id,
        )


def configure(
        server_url: str,
        polling_sleep_seconds: Optional[int] = None,
        request_logger: Optional[object] = None,
        target_audience_client_id: Optional[str] = None,
) -> PullQueueWorkerConfiguration:
    config = _ConfigurationFactory().build(
        server_url=server_url,
        polling_sleep_seconds=polling_sleep_seconds,
        request_logger=request_logger,
        target_audience_client_id=target_audience_client_id,
    )

    injector.binder.bind(PullQueueWorkerConfiguration, to=config, scope=singleton)
    injector.binder.install(pullqueue_worker_bind)

    return config


def get_config() -> PullQueueWorkerConfiguration:
    return injector.get(PullQueueWorkerConfiguration)
