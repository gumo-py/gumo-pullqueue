class PullQueueError(Exception):
    pass


class LeaseError(PullQueueError):
    pass


class AlreadyLeasedError(LeaseError):
    pass


class AlreadyDeletedError(LeaseError):
    pass
