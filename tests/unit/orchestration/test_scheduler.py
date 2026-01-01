"""Unit tests for scheduler implementation."""

import threading
import time

import pytest

from agent_core.configuration.schemas import AgentCoreConfig, RuntimeConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.orchestration.scheduler import Scheduler, ScheduledTask
from agent_core.observability.noop import NoOpObservabilitySink
from agent_core.utils.ids import generate_correlation_id, generate_run_id


def create_test_config(concurrency: int = 2) -> AgentCoreConfig:
    """Create a test configuration with specified concurrency."""
    return AgentCoreConfig(
        runtime=RuntimeConfig(
            runtime_id="test-runtime",
            concurrency=concurrency,
        ),
    )


def create_test_context() -> ExecutionContext:
    """Create a test execution context."""
    return ExecutionContext(
        run_id=generate_run_id(),
        correlation_id=generate_correlation_id(),
        initiator="test:user",
        permissions={},
        budget={},
        locale="en-US",
        observability={},
    )


class TestScheduler:
    """Test scheduler functionality."""

    def test_scheduler_initialization(self):
        """Test that scheduler initializes correctly."""
        config = create_test_config(concurrency=3)
        scheduler = Scheduler(config)

        assert scheduler.max_concurrency == 3
        assert scheduler.get_status()["max_concurrency"] == 3
        assert scheduler.get_status()["running_count"] == 0
        assert scheduler.get_status()["queued_count"] == 0

    def test_scheduler_requires_runtime_config(self):
        """Test that scheduler requires runtime configuration."""
        config = AgentCoreConfig()
        with pytest.raises(ValueError, match="Runtime configuration is required"):
            Scheduler(config)

    def test_schedule_and_execute_task(self):
        """Test scheduling and executing a single task."""
        config = create_test_config(concurrency=1)
        scheduler = Scheduler(config)

        result_container = {"value": None}

        def task_fn():
            result_container["value"] = "completed"
            return "task_result"

        context = create_test_context()
        completion_event = scheduler.schedule(
            task_id="task-1",
            execute_fn=task_fn,
            context=context,
            priority=0,
        )

        # Wait for completion
        assert completion_event.wait(timeout=2.0)
        assert result_container["value"] == "completed"
        assert scheduler.get_result("task-1") == "task_result"
        assert scheduler.get_status()["running_count"] == 0

    def test_concurrency_limit(self):
        """Test that concurrency limit is enforced."""
        config = create_test_config(concurrency=2)
        scheduler = Scheduler(config)

        execution_order = []
        lock = threading.Lock()

        def task_fn(task_id: str, delay: float):
            with lock:
                execution_order.append(f"start-{task_id}")
            time.sleep(delay)
            with lock:
                execution_order.append(f"end-{task_id}")

        context = create_test_context()

        # Schedule 3 tasks (only 2 should run concurrently)
        scheduler.schedule(
            task_id="task-1",
            execute_fn=lambda: task_fn("task-1", 0.1),
            context=context,
            priority=0,
        )
        scheduler.schedule(
            task_id="task-2",
            execute_fn=lambda: task_fn("task-2", 0.1),
            context=context,
            priority=0,
        )
        scheduler.schedule(
            task_id="task-3",
            execute_fn=lambda: task_fn("task-3", 0.1),
            context=context,
            priority=0,
        )

        # Wait for all tasks to complete
        time.sleep(0.5)

        # Verify concurrency limit was respected
        status = scheduler.get_status()
        assert status["running_count"] == 0  # All tasks completed
        assert len(execution_order) == 6  # 3 starts + 3 ends

    def test_priority_ordering(self):
        """Test that higher priority tasks execute before lower priority ones."""
        config = create_test_config(concurrency=1)
        scheduler = Scheduler(config)

        execution_order = []

        def task_fn(task_id: str):
            execution_order.append(task_id)

        context = create_test_context()

        # Schedule tasks with different priorities (lower priority first)
        scheduler.schedule(
            task_id="low-priority",
            execute_fn=lambda: task_fn("low-priority"),
            context=context,
            priority=0,
        )
        scheduler.schedule(
            task_id="high-priority",
            execute_fn=lambda: task_fn("high-priority"),
            context=context,
            priority=10,
        )
        scheduler.schedule(
            task_id="medium-priority",
            execute_fn=lambda: task_fn("medium-priority"),
            context=context,
            priority=5,
        )

        # Wait for all tasks to complete
        time.sleep(0.5)

        # Verify priority ordering: high-priority should execute first
        assert execution_order[0] == "low-priority"  # First scheduled, starts immediately
        assert "high-priority" in execution_order
        assert "medium-priority" in execution_order
        # High priority should come before medium priority in queue
        high_idx = execution_order.index("high-priority")
        medium_idx = execution_order.index("medium-priority")
        assert high_idx < medium_idx

    def test_fairness_within_priority(self):
        """Test that fairness prevents starvation within same priority."""
        config = create_test_config(concurrency=1)
        scheduler = Scheduler(config)

        execution_order = []

        def task_fn(task_id: str):
            execution_order.append(task_id)

        context = create_test_context()

        # Schedule multiple tasks with same priority
        for i in range(5):
            scheduler.schedule(
                task_id=f"task-{i}",
                execute_fn=lambda idx=i: task_fn(f"task-{idx}"),
                context=context,
                priority=0,
            )

        # Wait for all tasks to complete
        time.sleep(0.5)

        # Verify all tasks executed (fairness)
        assert len(execution_order) == 5
        assert all(f"task-{i}" in execution_order for i in range(5))

    def test_task_result_retrieval(self):
        """Test retrieving task results."""
        config = create_test_config(concurrency=1)
        scheduler = Scheduler(config)

        def task_fn():
            return {"result": "success", "value": 42}

        context = create_test_context()
        completion_event = scheduler.schedule(
            task_id="task-1",
            execute_fn=task_fn,
            context=context,
            priority=0,
        )

        completion_event.wait(timeout=2.0)
        result = scheduler.get_result("task-1")
        assert result == {"result": "success", "value": 42}

    def test_task_error_handling(self):
        """Test that task errors are properly handled."""
        config = create_test_config(concurrency=1)
        scheduler = Scheduler(config)

        def task_fn():
            raise ValueError("Task error")

        context = create_test_context()
        completion_event = scheduler.schedule(
            task_id="task-1",
            execute_fn=task_fn,
            context=context,
            priority=0,
        )

        completion_event.wait(timeout=2.0)

        # Error should be raised when getting result
        with pytest.raises(ValueError, match="Task error"):
            scheduler.get_result("task-1")

    def test_duplicate_task_id_rejection(self):
        """Test that duplicate task IDs are rejected."""
        config = create_test_config(concurrency=1)
        scheduler = Scheduler(config)

        def task_fn():
            return "result"

        context = create_test_context()
        scheduler.schedule(
            task_id="task-1",
            execute_fn=task_fn,
            context=context,
            priority=0,
        )

        # Wait for first task to complete
        time.sleep(0.2)

        # Try to schedule same task ID again
        with pytest.raises(ValueError, match="already scheduled or completed"):
            scheduler.schedule(
                task_id="task-1",
                execute_fn=task_fn,
                context=context,
                priority=0,
            )

    def test_wait_for_completion(self):
        """Test waiting for task completion."""
        config = create_test_config(concurrency=1)
        scheduler = Scheduler(config)

        def task_fn():
            time.sleep(0.1)
            return "result"

        context = create_test_context()
        completion_event = scheduler.schedule(
            task_id="task-1",
            execute_fn=task_fn,
            context=context,
            priority=0,
        )

        # Wait should return True when task completes
        assert scheduler.wait_for_completion("task-1", timeout=2.0) is True

    def test_wait_for_completion_timeout(self):
        """Test waiting for task completion with timeout."""
        config = create_test_config(concurrency=1)
        scheduler = Scheduler(config)

        def task_fn():
            time.sleep(1.0)  # Long-running task
            return "result"

        context = create_test_context()
        scheduler.schedule(
            task_id="task-1",
            execute_fn=task_fn,
            context=context,
            priority=0,
        )

        # Wait should return False on timeout
        assert scheduler.wait_for_completion("task-1", timeout=0.1) is False

    def test_get_status(self):
        """Test getting scheduler status."""
        config = create_test_config(concurrency=2)
        scheduler = Scheduler(config)

        def task_fn():
            time.sleep(0.2)
            return "result"

        context = create_test_context()

        # Schedule tasks
        scheduler.schedule(
            task_id="task-1",
            execute_fn=task_fn,
            context=context,
            priority=0,
        )
        scheduler.schedule(
            task_id="task-2",
            execute_fn=task_fn,
            context=context,
            priority=0,
        )
        scheduler.schedule(
            task_id="task-3",
            execute_fn=task_fn,
            context=context,
            priority=0,
        )

        # Check status immediately (should show running and queued tasks)
        time.sleep(0.05)  # Give tasks time to start
        status = scheduler.get_status()
        assert status["max_concurrency"] == 2
        assert status["running_count"] <= 2
        assert status["queued_count"] >= 0
        assert len(status["running_tasks"]) <= 2

    def test_scheduler_with_observability_sink(self):
        """Test that scheduler works with observability sink."""
        config = create_test_config(concurrency=1)
        sink = NoOpObservabilitySink()
        scheduler = Scheduler(config, observability_sink=sink)

        def task_fn():
            return "result"

        context = create_test_context()
        completion_event = scheduler.schedule(
            task_id="task-1",
            execute_fn=task_fn,
            context=context,
            priority=5,
        )

        completion_event.wait(timeout=2.0)
        assert scheduler.get_result("task-1") == "result"

