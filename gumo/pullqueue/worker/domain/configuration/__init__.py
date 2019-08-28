import dataclasses
import os
from typing import Optional


@dataclasses.dataclass(frozen=True)
class PullQueueWorkerConfiguration:
    server_url: str
    polling_sleep_seconds: int
    request_logger: object = None
    target_audience_client_id: Optional[str] = None
    worker_name: str = dataclasses.field(default_factory=lambda: f'pid={os.getpid()}')
