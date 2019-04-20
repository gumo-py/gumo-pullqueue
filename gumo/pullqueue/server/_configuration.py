from logging import getLogger
from typing import Optional

from gumo.core.injector import injector
from gumo.pullqueue.server.domain.configuration import PullQueueConfiguration
from gumo.pullqueue.server.bind import pullqueue_bind

logger = getLogger(__name__)


class ConfigurationFactory:
    @classmethod
    def build(
            cls,
            default_queue_name: Optional[str] = None,
    ) -> PullQueueConfiguration:
        if default_queue_name is None:
            return PullQueueConfiguration()

        return PullQueueConfiguration(
            default_queue_name=default_queue_name
        )


def configure(
        default_queue_name: str,
) -> PullQueueConfiguration:
    config = ConfigurationFactory.build(
        default_queue_name=default_queue_name,
    )
    logger.debug(f'Gumo.PullQueue is configured, config = {config}')

    injector.binder.bind(PullQueueConfiguration, config)
    injector.binder.install(pullqueue_bind)

    return config
