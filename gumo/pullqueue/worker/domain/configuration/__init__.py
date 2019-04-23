import dataclasses
from typing import Optional


@dataclasses.dataclass(frozen=True)
class PullQueueWorkerConfiguration:
    server_url: str
    polling_sleep_seconds: int
    request_logger: object = None
    target_audience_client_id: Optional[str] = None
