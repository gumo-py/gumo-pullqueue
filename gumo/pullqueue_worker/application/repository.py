from logging import getLogger
from typing import List

from gumo.core import EntityKey
from gumo.pullqueue import PullTask

logger = getLogger(__name__)


class PullTaskRemoteRepository:
    def __init__(self):
        pass

    def lease_tasks(
            self,
            queue_name: str,
            size: int = 100,
    ) -> List[PullTask]:
        raise NotImplementedError()

    def delete_tasks(
            self,
            keys: List[EntityKey],
    ):
        raise NotImplementedError()
