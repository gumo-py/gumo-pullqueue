import dataclasses


@dataclasses.dataclass(frozen=True)
class PullQueueWorkerConfiguration:
    server_url: str
    polling_sleep_seconds: int
