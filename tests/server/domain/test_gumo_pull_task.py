import pytest
import datetime

from gumo.core import EntityKeyFactory

from gumo.pullqueue.domain import PullTask
from gumo.pullqueue.server.domain import PullTaskState
from gumo.pullqueue.server.domain import PullTaskStatus
from gumo.pullqueue.server.domain import PullTaskWorker
from gumo.pullqueue.server.domain import GumoPullTask
from gumo.pullqueue.server.domain import TaskEvent
from gumo.pullqueue.server.domain import LeaseRequest
from gumo.pullqueue.server.domain import LeaseExtendRequest
from gumo.pullqueue.server.domain import SuccessRequest
from gumo.pullqueue.server.domain import FailureRequest


class TestPullTask:
    def test_build_success(self):
        task = PullTask(
            key=EntityKeyFactory().build_for_new(kind='PullTask'),
            queue_name='test'
        )

        assert isinstance(task, PullTask)
        assert isinstance(task.to_json(), dict)
        assert PullTask.from_json(task.to_json()) == task


class TestPullTaskState:
    def test_build_success(self):
        state = PullTaskState(
            status=PullTaskStatus.available,
        )
        assert state.status == PullTaskStatus.available
        assert state.execution_count == 0
        assert state.retry_count == 0
        assert state.last_executed_at is None
        assert state.next_executed_at is None
        assert state.leased_at is None
        assert state.lease_expires_at is None
        assert state.leased_by is None

    def test_with_status(self):
        state = PullTaskState(status=PullTaskStatus.available)
        assert state.with_status(
            new_status=PullTaskStatus.leased
        ).status == PullTaskStatus.leased

    def test_with_lease_info(self):
        now = datetime.datetime.utcnow()
        state = PullTaskState(status=PullTaskStatus.available)
        new_state = state.with_lease_info(
            leased_at=now,
            lease_expires_at=now + datetime.timedelta(seconds=300),
            leased_by=PullTaskWorker(address='127.0.0.1', name='worker:1')
        )

        assert new_state != state

    def test_increment_count_if_needed(self):
        state = PullTaskState(status=PullTaskStatus.available)
        new_state = state.increment_count_if_needed()

        assert new_state != state
        assert new_state.execution_count == 1
        assert new_state.retry_count == 0

        next_state = new_state.increment_count_if_needed()
        assert next_state != new_state
        assert next_state.execution_count == 2
        assert next_state.retry_count == 1


class TestGumoPullTask:
    def build(self) -> GumoPullTask:
        return GumoPullTask(
            task=PullTask(
                key=EntityKeyFactory().build_for_new(kind='PullTask'),
                queue_name='test'
            ),
            state=PullTaskState(),
            event_logs=[]
        )

    def test_build_success(self):
        t = GumoPullTask(
            task=PullTask(
                key=EntityKeyFactory().build_for_new(kind='PullTask'),
                queue_name='test'
            ),
            state=PullTaskState(),
            event_logs=[]
        )
        assert isinstance(t, GumoPullTask)

    def test_with_status(self):
        task = self.build()
        changed = task.with_status(new_status=PullTaskStatus.leased)

        assert task != changed
        assert task.state.status != changed.state.status

    def test_add_event_log(self):
        now = datetime.datetime.utcnow()
        task = self.build()
        changed = task.add_event_log(
            event_log=TaskEvent(
                event_at=now,
                worker=PullTaskWorker(address='127.0.0.1', name='worker:1')
            )
        )

        assert len(task.event_logs) == 0
        assert len(changed.event_logs) == 1


class TestLeaseRequest:
    def build(self) -> GumoPullTask:
        return GumoPullTask(
            task=PullTask(
                key=EntityKeyFactory().build_for_new(kind='PullTask'),
                queue_name='test'
            ),
            state=PullTaskState(),
            event_logs=[]
        )

    def test_build_success(self):
        now = datetime.datetime.utcnow()
        task = self.build()
        event = LeaseRequest(
            event_at=now,
            worker=PullTaskWorker(address='127.0.0.1', name='worker:1'),
            lease_time=300
        )

        next_task = event.build_next(task=task)

        assert task != next_task
        assert len(next_task.event_logs) == len(task.event_logs) + 1
        assert next_task.state.status == PullTaskStatus.leased
        assert next_task.state.leased_at == now
        assert next_task.state.lease_expires_at == now + datetime.timedelta(seconds=300)


class TestLeaseExtendRequest:
    def build(self) -> GumoPullTask:
        return GumoPullTask(
            task=PullTask(
                key=EntityKeyFactory().build_for_new(kind='PullTask'),
                queue_name='test'
            ),
            state=PullTaskState(),
            event_logs=[]
        )

    def build_leased_task(self) -> GumoPullTask:
        now = datetime.datetime.utcnow()
        task = self.build()
        event = LeaseRequest(
            event_at=now,
            worker=PullTaskWorker(address='127.0.0.1', name='worker:1'),
            lease_time=300
        )

        return event.build_next(task=task)

    def test_build_success(self):
        now = datetime.datetime.utcnow()
        leased_task = self.build_leased_task()
        event = LeaseExtendRequest(
            event_at=now,
            worker=PullTaskWorker(address='127.0.0.1', name='worker:1'),
            lease_extend_time=300,
        )

        next_task = event.build_next(task=leased_task, now=now)

        assert next_task != leased_task
        assert len(next_task.event_logs) == len(leased_task.event_logs) + 1
        assert next_task.state.status == leased_task.state.status
        assert next_task.state.leased_at == leased_task.state.leased_at
        assert next_task.state.lease_expires_at == now + datetime.timedelta(seconds=300)
        assert next_task.state.leased_by == leased_task.state.leased_by

    def test_build_failed_from_available(self):
        task = self.build()
        now = datetime.datetime.utcnow()
        event = LeaseExtendRequest(
            event_at=now,
            worker=PullTaskWorker(address='127.0.0.1', name='worker:1'),
            lease_extend_time=300,
        )

        with pytest.raises(ValueError):
            event.build_next(task=task)


class TestSuccessRequest:
    def build(self) -> GumoPullTask:
        return GumoPullTask(
            task=PullTask(
                key=EntityKeyFactory().build_for_new(kind='PullTask'),
                queue_name='test'
            ),
            state=PullTaskState(),
            event_logs=[]
        )

    def build_leased_task(self) -> GumoPullTask:
        now = datetime.datetime.utcnow()
        task = self.build()
        event = LeaseRequest(
            event_at=now,
            worker=PullTaskWorker(address='127.0.0.1', name='worker:1'),
            lease_time=300
        )

        return event.build_next(task=task)

    def test_build_success(self):
        now = datetime.datetime.utcnow()
        leased_task = self.build_leased_task()
        event = SuccessRequest(
            event_at=now,
            worker=PullTaskWorker(address='127.0.0.1', name='worker:1'),
        )

        next_task = event.build_next(task=leased_task)

        assert next_task != leased_task
        assert len(next_task.event_logs) == len(leased_task.event_logs) + 1
        assert next_task.state.status == PullTaskStatus.deleted

    def test_build_failed_from_available(self):
        task = self.build()
        now = datetime.datetime.utcnow()
        event = SuccessRequest(
            event_at=now,
            worker=PullTaskWorker(address='127.0.0.1', name='worker:1'),
        )

        with pytest.raises(ValueError):
            event.build_next(task=task)


class TestFailureRequest:
    def build(self) -> GumoPullTask:
        return GumoPullTask(
            task=PullTask(
                key=EntityKeyFactory().build_for_new(kind='PullTask'),
                queue_name='test'
            ),
            state=PullTaskState(),
            event_logs=[]
        )

    def build_leased_task(self) -> GumoPullTask:
        now = datetime.datetime.utcnow()
        task = self.build()
        event = LeaseRequest(
            event_at=now,
            worker=PullTaskWorker(address='127.0.0.1', name='worker:1'),
            lease_time=300
        )

        return event.build_next(task=task)

    def test_build_success(self):
        now = datetime.datetime.utcnow()
        leased_task = self.build_leased_task()
        event = FailureRequest(
            event_at=now,
            worker=PullTaskWorker(address='127.0.0.1', name='worker:1'),
            message='something failed reason message.'
        )

        next_task = event.build_next(task=leased_task, now=now)

        assert next_task != leased_task
        assert next_task.state.status == PullTaskStatus.available
        assert len(next_task.event_logs) == len(leased_task.event_logs) + 1

        assert next_task.state.leased_at is None
        assert next_task.state.lease_expires_at is None
        assert next_task.state.leased_by is None

        assert next_task.state.last_executed_at == leased_task.state.leased_at
        assert next_task.state.next_executed_at >= now + datetime.timedelta(seconds=60)
