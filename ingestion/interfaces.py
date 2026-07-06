"""
Abstract Interfaces for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: ISA-95 Part 2 Edge Integration Layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import threading
from .models import StandardizedTelemetryModel


class IDatabaseWriter(ABC):
    """Abstract interface decouple pipeline processing from database drivers."""
    @abstractmethod
    def save_telemetry_record(self, record: StandardizedTelemetryModel) -> None:
        """Persists a standardized time-series telemetry record."""
        pass

    @abstractmethod
    def save_bulk_telemetry_records(self, records: List[StandardizedTelemetryModel]) -> None:
        """Executes a high-throughput atomic batch insert statement."""
        pass

    @abstractmethod
    def save_alert_event(self, event_raw: Dict[str, Any]) -> None:
        """Persists a parsed and validated system alert event notification."""
        pass

    # Backwards compatibility methods
    def write(self, record: Any) -> bool:
        self.save_telemetry_record(record)
        return True

    def write_batch(self, records: List[Any]) -> int:
        self.save_bulk_telemetry_records(records)
        return len(records)


class InMemoryDatabaseWriter(IDatabaseWriter):
    """Concrete thread-safe in-memory database writer implementation for testing."""
    def __init__(self):
        self.records: List[StandardizedTelemetryModel] = []
        self.alerts: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def save_telemetry_record(self, record: StandardizedTelemetryModel) -> None:
        with self._lock:
            self.records.append(record)

    def save_bulk_telemetry_records(self, records: List[StandardizedTelemetryModel]) -> None:
        with self._lock:
            self.records.extend(records)

    def save_alert_event(self, event_raw: Dict[str, Any]) -> None:
        with self._lock:
            self.alerts.append(event_raw)
