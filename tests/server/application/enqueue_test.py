from gumo.core.injector import injector

from gumo.pullqueue.server.application.enqueue import enqueue
from gumo.pullqueue.server.application.repository import GumoPullTaskRepository
from gumo.pullqueue.server.domain import PullTask


def test_enqueue():
    repo = injector.get(GumoPullTaskRepository)  # type: GumoPullTaskRepository
    before = repo.total_count()

    t = enqueue(
        payload={'key': 'value'},
        in_seconds=10,
        queue_name='changed-server',
        tag='sample-tag'
    )

    assert isinstance(t, PullTask)
    assert t.queue_name == 'changed-server'
    assert t.payload == {'key': 'value'}
    assert t.tag == 'sample-tag'

    after = repo.total_count()

    assert before + 1 == after

    repo.purge()
    assert repo.total_count() == 0
