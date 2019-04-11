from logging import getLogger

from gumo.pullqueue._configuration import configure
from gumo.pullqueue.domain.configuration import PullQueueConfiguration


__all__ = [
    configure.__name__,
    PullQueueConfiguration.__name__,
]

logger = getLogger('gumo.pullqueue')
