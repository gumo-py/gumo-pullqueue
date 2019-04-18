import datetime
from gumo.core.injector import injector

from gumo.pullqueue.server.application.enqueue import enqueue
from gumo.pullqueue.server.application.repository import GumoPullTaskRepository


def test_fetch_available_tasks():
    # setup
    repo = injector.get(GumoPullTaskRepository)  # type: GumoPullTaskRepository
    repo.purge()

    assert repo.total_count() == 0

    current_task = enqueue(
        payload={'key': 'value1'},
        in_seconds=0,
        queue_name='server',
    )
    future_task = enqueue(
        payload={'key': 'value2'},
        in_seconds=30,
        queue_name='server',
    )

    assert repo.total_count() == 2

    current_tasks = repo.fetch_available_tasks(
        queue_name='server'
    )
    assert len(current_tasks) == 1
    assert current_tasks[0].task == current_task

    assert len(
        repo.fetch_available_tasks(
            queue_name='server-invalid'
        )
    ) == 0

    future_tasks = repo.fetch_available_tasks(
        queue_name='server',
        now=datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
    )
    assert len(future_tasks) == 2
    assert future_tasks[0].task == current_task
    assert future_tasks[1].task == future_task

    future_tasks_with_limit_1 = repo.fetch_available_tasks(
        queue_name='server',
        now=datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        size=1
    )
    assert len(future_tasks_with_limit_1) == 1

    repo.purge()
