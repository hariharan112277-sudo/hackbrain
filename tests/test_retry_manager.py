import pytest
from ingestion.retry_manager import RetryManager, retry_on_failure


def test_retry_manager_success_after_retries():
    counter = {"attempts": 0}

    def flaky_func():
        counter["attempts"] += 1
        if counter["attempts"] < 3:
            raise ValueError("Transient error")
        return "Success"

    manager = RetryManager(max_retries=3, base_delay_sec=0.01)
    result = manager.execute(flaky_func)
    assert result == "Success"
    assert counter["attempts"] == 3


def test_retry_manager_exhausted():
    def failing_func():
        raise RuntimeError("Persistent failure")

    manager = RetryManager(max_retries=2, base_delay_sec=0.01)
    with pytest.raises(RuntimeError):
        manager.execute(failing_func)


def test_retry_decorator():
    counter = {"attempts": 0}

    @retry_on_failure(max_retries=2, base_delay=0.01, exceptions=(KeyError,))
    def test_op():
        counter["attempts"] += 1
        if counter["attempts"] == 1:
            raise KeyError("Key transient")
        return 42

    assert test_op() == 42
