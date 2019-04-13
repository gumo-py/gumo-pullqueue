from gumo.pullqueue.application.enqueue import enqueue
from gumo.pullqueue.domain import PullTask


def test_enqueue():
    t = enqueue(
        payload={'key': 'value'},
        in_seconds=10,
        queue_name='changed-pullqueue',
        tag='sample-tag'
    )

    assert isinstance(t, PullTask)
    assert t.queue_name == 'changed-pullqueue'
    assert t.payload == {'key': 'value'}
    assert t.tag == 'sample-tag'
