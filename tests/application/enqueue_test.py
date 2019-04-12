from gumo.pullqueue.application import enqueue


def test_enqueue():
    t = enqueue(
        payload={'key': 'value'},
        in_seconds=10,
        queue_name='changed-pullqueue',
        tag='sample-tag'
    )

    assert t is None
