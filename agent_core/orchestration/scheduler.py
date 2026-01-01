"""Scheduler for priority-based execution with thread-based concurrency.

Implements scheduling with numeric priorities, concurrency limits, fairness
rules, and observability for scheduling decisions.
"""

import heapq
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from agent_core.configuration.schemas import AgentCoreConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.observability import ComponentType, CorrelationFields
from agent_core.observability.interface import ObservabilitySink
from agent_core.observability.logging import get_logger


@dataclass
class ScheduledTask:
    """Represents a task scheduled for execution.

    Attributes:
        priority: Numeric priority (higher = higher priority).
        task_id: Unique identifier for this task.
        execute_fn: Callable to execute the task.
        context: Execution context for the task.
        enqueue_time: Timestamp when task was enqueued.
        fairness_counter: Counter to ensure fairness within same priority.
    """

    priority: int
    task_id: str
    execute_fn: Callable[[], Any]
    context: ExecutionContext
    enqueue_time: float = field(default_factory=time.time)
    fairness_counter: int = 0

    def __lt__(self, other: "ScheduledTask") -> bool:
        """Compare tasks for priority queue ordering.

        Higher priority first, then by fairness counter (FIFO within same priority).
        """
        if self.priority != other.priority:
            return self.priority > other.priority  # Higher priority first
        return self.fairness_counter < other.fairness_counter  # FIFO within same priority


class Scheduler:
    """Scheduler with priority-based execution and thread-based concurrency.

    Manages concurrent execution of tasks with:
    - Numeric priorities (higher priority preempts lower)
    - Concurrency limits from runtime configuration
    - Fairness rules to prevent starvation
    - Observable scheduling decisions

    Thread-based only (no async in v1).
    """

    def __init__(
        self,
        config: AgentCoreConfig,
        observability_sink: ObservabilitySink | None = None,
    ):
        """Initialize scheduler.

        Args:
            config: Runtime configuration containing concurrency limits.
            observability_sink: Optional observability sink for scheduling signals.
        """
        if config.runtime is None:
            raise ValueError("Runtime configuration is required for scheduler.")

        self.config = config
        self.max_concurrency = config.runtime.concurrency
        self.observability_sink = observability_sink

        # Thread-safe data structures
        self._lock = threading.RLock()
        self._pending_queue: list[ScheduledTask] = []  # Priority queue (heap)
        self._running_tasks: dict[str, threading.Thread] = {}
        self._task_results: dict[str, Any] = {}
        self._task_errors: dict[str, Exception] = {}
        self._task_completion_events: dict[str, threading.Event] = {}

        # Fairness tracking: counter per priority level
        self._fairness_counters: defaultdict[int, int] = defaultdict(int)

        # Create correlation for observability
        correlation = CorrelationFields(
            run_id="scheduler",  # Scheduler doesn't have a run_id
            correlation_id="scheduler",
            component_type=ComponentType.RUNTIME,
            component_id="scheduler",
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.logger = get_logger("agent_core.orchestration.scheduler", correlation)

        self.logger.info(
            "Scheduler initialized",
            extra={
                "max_concurrency": self.max_concurrency,
            },
        )

    def schedule(
        self,
        task_id: str,
        execute_fn: Callable[[], Any],
        context: ExecutionContext,
        priority: int = 0,
    ) -> threading.Event:
        """Schedule a task for execution.

        Args:
            task_id: Unique identifier for this task.
            execute_fn: Callable to execute the task.
            context: Execution context for the task.
            priority: Numeric priority (higher = higher priority). Defaults to 0.

        Returns:
            threading.Event that will be set when the task completes.
            The event can be used to wait for task completion.

        Notes:
            - Tasks are queued if concurrency limit is reached.
            - Higher priority tasks preempt lower priority ones in the queue.
            - Fairness ensures FIFO ordering within the same priority level.
        """
        with self._lock:
            # Check if task already exists (running, queued, or completed)
            if task_id in self._running_tasks:
                raise ValueError(f"Task '{task_id}' is already running.")
            if task_id in self._task_completion_events:
                raise ValueError(f"Task '{task_id}' is already scheduled or completed.")

            # Get fairness counter for this priority
            fairness_counter = self._fairness_counters[priority]
            self._fairness_counters[priority] += 1

            # Create scheduled task
            task = ScheduledTask(
                priority=priority,
                task_id=task_id,
                execute_fn=execute_fn,
                context=context,
                fairness_counter=fairness_counter,
            )

            # Create completion event
            completion_event = threading.Event()
            self._task_completion_events[task_id] = completion_event

            # Emit observability signal
            self._emit_scheduling_decision(
                task_id=task_id,
                priority=priority,
                decision="queued",
                reason="concurrency_limit"
                if len(self._running_tasks) >= self.max_concurrency
                else "immediate",
            )

            # Check if we can execute immediately
            if len(self._running_tasks) < self.max_concurrency:
                # Execute immediately
                self._start_task(task)
            else:
                # Queue for later execution
                heapq.heappush(self._pending_queue, task)
                self.logger.info(
                    "Task queued",
                    extra={
                        "task_id": task_id,
                        "priority": priority,
                        "queue_size": len(self._pending_queue),
                    },
                )

            return completion_event

    def _start_task(self, task: ScheduledTask) -> None:
        """Start executing a task in a separate thread.

        Args:
            task: Scheduled task to execute.
        """

        def task_wrapper() -> None:
            """Wrapper function to execute task and handle completion."""
            try:
                self.logger.info(
                    "Task started", extra={"task_id": task.task_id, "priority": task.priority}
                )

                # Execute the task
                result = task.execute_fn()

                # Store result
                with self._lock:
                    self._task_results[task.task_id] = result
                    self._task_errors.pop(task.task_id, None)  # Clear any previous error

            except Exception as e:
                # Store error
                with self._lock:
                    self._task_errors[task.task_id] = e
                    self._task_results.pop(task.task_id, None)  # Clear any previous result

                self.logger.error(
                    "Task execution failed",
                    extra={"task_id": task.task_id, "error": str(e)},
                )
            finally:
                # Mark task as complete
                with self._lock:
                    self._running_tasks.pop(task.task_id, None)

                    # Signal completion (but keep event for result retrieval)
                    completion_event = self._task_completion_events.get(task.task_id)
                    if completion_event:
                        completion_event.set()
                    # Don't remove completion event - keep it for result retrieval

                    # Emit observability signal
                    self._emit_scheduling_decision(
                        task_id=task.task_id,
                        priority=task.priority,
                        decision="completed",
                        reason="task_finished",
                    )

                    # Try to start next queued task
                    self._try_start_next_task()

        # Create and start thread
        thread = threading.Thread(target=task_wrapper, name=f"scheduler-task-{task.task_id}")
        thread.daemon = True  # Allow main process to exit even if threads are running

        with self._lock:
            self._running_tasks[task.task_id] = thread

        thread.start()

        self.logger.info(
            "Task execution started",
            extra={
                "task_id": task.task_id,
                "priority": task.priority,
                "running_count": len(self._running_tasks),
            },
        )

    def _try_start_next_task(self) -> None:
        """Try to start the next queued task if concurrency allows."""
        with self._lock:
            if len(self._running_tasks) >= self.max_concurrency:
                return  # At capacity

            if not self._pending_queue:
                return  # No queued tasks

            # Get highest priority task from queue
            next_task = heapq.heappop(self._pending_queue)

            # Start execution
            self._start_task(next_task)

            self.logger.info(
                "Next queued task started",
                extra={
                    "task_id": next_task.task_id,
                    "priority": next_task.priority,
                    "queue_size": len(self._pending_queue),
                },
            )

    def get_result(self, task_id: str, timeout: float | None = None) -> Any:
        """Get the result of a completed task.

        Args:
            task_id: Task identifier.
            timeout: Optional timeout in seconds. If None, waits indefinitely.

        Returns:
            Task result if available.

        Raises:
            KeyError: If task_id is not found.
            TimeoutError: If timeout is reached.
            Exception: If task execution raised an exception.
        """
        # Wait for completion if task is still running
        completion_event = self._task_completion_events.get(task_id)
        if completion_event is not None:
            if not completion_event.wait(timeout=timeout):
                raise TimeoutError(f"Task '{task_id}' did not complete within timeout.")

        # Check for errors
        with self._lock:
            if task_id in self._task_errors:
                raise self._task_errors[task_id]

            if task_id in self._task_results:
                return self._task_results[task_id]

            # Task not found or not completed
            if (
                task_id not in self._task_completion_events
                and task_id not in self._task_results
                and task_id not in self._task_errors
            ):
                raise KeyError(f"Task '{task_id}' not found.")

            raise KeyError(f"Task '{task_id}' result not found.")

    def wait_for_completion(self, task_id: str, timeout: float | None = None) -> bool:
        """Wait for a task to complete.

        Args:
            task_id: Task identifier.
            timeout: Optional timeout in seconds. If None, waits indefinitely.

        Returns:
            True if task completed, False if timeout occurred or task not found.
        """
        completion_event = self._task_completion_events.get(task_id)
        if completion_event is None:
            # Check if task already completed (has result or error)
            with self._lock:
                if task_id in self._task_results or task_id in self._task_errors:
                    return True  # Already completed
            return False  # Task not found

        return completion_event.wait(timeout=timeout)

    def get_status(self) -> dict[str, Any]:
        """Get current scheduler status.

        Returns:
            Dictionary containing scheduler status information.
        """
        with self._lock:
            return {
                "max_concurrency": self.max_concurrency,
                "running_count": len(self._running_tasks),
                "queued_count": len(self._pending_queue),
                "running_tasks": list(self._running_tasks.keys()),
            }

    def _emit_scheduling_decision(
        self,
        task_id: str,
        priority: int,
        decision: str,
        reason: str,
    ) -> None:
        """Emit observability signal for scheduling decision.

        Args:
            task_id: Task identifier.
            priority: Task priority.
            decision: Decision made (e.g., "queued", "started", "completed").
            reason: Reason for the decision.
        """
        if self.observability_sink is None:
            return

        try:
            # Emit structured log
            self.logger.info(
                "Scheduling decision",
                extra={
                    "task_id": task_id,
                    "priority": priority,
                    "decision": decision,
                    "reason": reason,
                },
            )

            # Could also emit metrics or traces here if needed
            # For now, structured logging is sufficient for observability
        except Exception as e:
            # Observability failures should not break execution
            self.logger.warning(
                "Failed to emit scheduling observability signal",
                extra={"error": str(e)},
            )
