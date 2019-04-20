import dataclasses


@dataclasses.dataclass(frozen=True)
class PullQueueConfiguration:
    default_queue_name: str = 'server'
