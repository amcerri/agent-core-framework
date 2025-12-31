"""Unit tests for budget tracking and enforcement."""

import time

import pytest

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.governance.budget import BudgetEnforcer, BudgetExhaustedError, BudgetTracker
from agent_core.runtime.execution_context import create_execution_context


class TestBudgetTracker:
    """Test BudgetTracker."""

    def test_tracker_initialization(self):
        """Test budget tracker initialization."""
        context = create_execution_context(
            initiator="user:test",
            budget={"time_limit_seconds": 60, "call_limit": 100, "cost_limit": 10.0},
        )
        tracker = BudgetTracker(context)

        assert tracker.time_limit == 60
        assert tracker.call_limit == 100
        assert tracker.cost_limit == 10.0
        assert tracker.call_count == 0
        assert tracker.cost_accumulated == 0.0

    def test_tracker_initialization_no_limits(self):
        """Test tracker initialization with no budget limits."""
        context = create_execution_context(initiator="user:test", budget={})
        tracker = BudgetTracker(context)

        assert tracker.time_limit is None
        assert tracker.call_limit is None
        assert tracker.cost_limit is None

    def test_record_call(self):
        """Test recording calls."""
        context = create_execution_context(
            initiator="user:test",
            budget={"call_limit": 10},
        )
        tracker = BudgetTracker(context)

        assert tracker.get_call_count() == 0
        tracker.record_call()
        assert tracker.get_call_count() == 1
        tracker.record_call()
        assert tracker.get_call_count() == 2

    def test_record_cost(self):
        """Test recording cost."""
        context = create_execution_context(
            initiator="user:test",
            budget={"cost_limit": 10.0},
        )
        tracker = BudgetTracker(context)

        assert tracker.get_cost_accumulated() == 0.0
        tracker.record_cost(1.5)
        assert tracker.get_cost_accumulated() == 1.5
        tracker.record_cost(2.3)
        assert tracker.get_cost_accumulated() == 3.8

    def test_record_cost_negative_raises_error(self):
        """Test that negative cost raises ValueError."""
        context = create_execution_context(initiator="user:test", budget={})
        tracker = BudgetTracker(context)

        with pytest.raises(ValueError, match="Cost cannot be negative"):
            tracker.record_cost(-1.0)

    def test_get_elapsed_time(self):
        """Test getting elapsed time."""
        context = create_execution_context(initiator="user:test", budget={})
        tracker = BudgetTracker(context)

        # Elapsed time should be very small immediately after initialization
        elapsed = tracker.get_elapsed_time()
        assert elapsed >= 0
        assert elapsed < 1.0  # Should be less than 1 second

        # Wait a bit and check again
        time.sleep(0.1)
        elapsed_after = tracker.get_elapsed_time()
        assert elapsed_after >= elapsed
        assert elapsed_after >= 0.1

    def test_get_budget_status(self):
        """Test getting budget status."""
        context = create_execution_context(
            initiator="user:test",
            budget={"time_limit_seconds": 60, "call_limit": 100, "cost_limit": 10.0},
        )
        tracker = BudgetTracker(context)

        tracker.record_call()
        tracker.record_cost(2.5)

        status = tracker.get_budget_status()
        assert status["time_limit"] == 60
        assert status["call_limit"] == 100
        assert status["call_count"] == 1
        assert status["cost_limit"] == 10.0
        assert status["cost_accumulated"] == 2.5
        assert "time_consumed" in status


class TestBudgetEnforcer:
    """Test BudgetEnforcer."""

    def test_check_budget_no_limits(self):
        """Test budget check with no limits."""
        context = create_execution_context(initiator="user:test", budget={})
        tracker = BudgetTracker(context)
        enforcer = BudgetEnforcer(tracker)

        # Should not raise when no limits are set
        enforcer.check_budget()

    def test_check_budget_time_exhausted(self):
        """Test budget check when time limit is exhausted."""
        context = create_execution_context(
            initiator="user:test",
            budget={"time_limit_seconds": 0.1},
        )
        tracker = BudgetTracker(context)
        enforcer = BudgetEnforcer(tracker)

        # Wait for time limit to be exceeded
        time.sleep(0.15)

        with pytest.raises(BudgetExhaustedError) as exc_info:
            enforcer.check_budget()

        assert exc_info.value.budget_type == "time"
        assert exc_info.value.limit == 0.1
        assert exc_info.value.consumed >= 0.1

    def test_check_budget_call_exhausted(self):
        """Test budget check when call limit is exhausted."""
        context = create_execution_context(
            initiator="user:test",
            budget={"call_limit": 3},
        )
        tracker = BudgetTracker(context)
        enforcer = BudgetEnforcer(tracker)

        # Record calls up to limit
        tracker.record_call()
        tracker.record_call()
        tracker.record_call()

        with pytest.raises(BudgetExhaustedError) as exc_info:
            enforcer.check_budget()

        assert exc_info.value.budget_type == "calls"
        assert exc_info.value.limit == 3
        assert exc_info.value.consumed == 3

    def test_check_budget_cost_exhausted(self):
        """Test budget check when cost limit is exhausted."""
        context = create_execution_context(
            initiator="user:test",
            budget={"cost_limit": 10.0},
        )
        tracker = BudgetTracker(context)
        enforcer = BudgetEnforcer(tracker)

        # Record cost up to limit
        tracker.record_cost(10.0)

        with pytest.raises(BudgetExhaustedError) as exc_info:
            enforcer.check_budget()

        assert exc_info.value.budget_type == "cost"
        assert exc_info.value.limit == 10.0
        assert exc_info.value.consumed == 10.0

    def test_check_budget_cost_exceeded(self):
        """Test budget check when cost limit is exceeded."""
        context = create_execution_context(
            initiator="user:test",
            budget={"cost_limit": 10.0},
        )
        tracker = BudgetTracker(context)
        enforcer = BudgetEnforcer(tracker)

        # Record cost exceeding limit
        tracker.record_cost(10.5)

        with pytest.raises(BudgetExhaustedError) as exc_info:
            enforcer.check_budget()

        assert exc_info.value.budget_type == "cost"
        assert exc_info.value.consumed == 10.5

    def test_check_budget_multiple_limits(self):
        """Test budget check with multiple limits."""
        context = create_execution_context(
            initiator="user:test",
            budget={"time_limit_seconds": 60, "call_limit": 100, "cost_limit": 10.0},
        )
        tracker = BudgetTracker(context)
        enforcer = BudgetEnforcer(tracker)

        # Should not raise when within all limits
        tracker.record_call()
        tracker.record_cost(5.0)
        enforcer.check_budget()

    def test_check_budget_time_priority(self):
        """Test that time limit is checked first."""
        context = create_execution_context(
            initiator="user:test",
            budget={"time_limit_seconds": 0.1, "call_limit": 1},
        )
        tracker = BudgetTracker(context)
        enforcer = BudgetEnforcer(tracker)

        # Wait for time limit
        time.sleep(0.15)

        # Should raise time error, not call error
        with pytest.raises(BudgetExhaustedError) as exc_info:
            enforcer.check_budget()

        assert exc_info.value.budget_type == "time"

    def test_to_error(self):
        """Test converting BudgetExhaustedError to structured Error."""
        context = create_execution_context(
            initiator="user:test",
            budget={"call_limit": 1},
        )
        tracker = BudgetTracker(context)
        enforcer = BudgetEnforcer(tracker)

        tracker.record_call()

        try:
            enforcer.check_budget()
        except BudgetExhaustedError as e:
            error = enforcer.to_error(e, source="test:component")
            assert error.error_type.value == "budget_exceeded"
            assert error.severity.value == "high"
            assert error.retryable is False
            assert error.metadata["budget_type"] == "calls"
            assert error.metadata["limit"] == 1
            assert error.metadata["consumed"] == 1

    def test_budget_enforcer_uses_tracker(self):
        """Test that enforcer uses the tracker."""
        context = create_execution_context(initiator="user:test", budget={})
        tracker = BudgetTracker(context)
        enforcer = BudgetEnforcer(tracker)

        assert enforcer.tracker == tracker
