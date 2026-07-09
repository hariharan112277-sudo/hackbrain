"""
Event Dispatcher Stage for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: Dependency Injection Call to IDatabaseWriter storage sinks.
"""

import queue
import concurrent.futures
import logging
from typing import List, Optional, Any
from .models import StandardizedTelemetryModel
from .interfaces import IDatabaseWriter
from .pipeline import TelemetryProcessingPipeline

logger = logging.getLogger("iob.dispatcher")


class TelemetryEventDispatcher:
    """Manages thread-safe queues and dispatches records out to injected writer plugins."""
    def __init__(self, processing_pipeline: Optional[TelemetryProcessingPipeline] = None, db_writer: Optional[IDatabaseWriter] = None, pool_workers: int = 4, writers: Optional[List[IDatabaseWriter]] = None):
        self.pipeline = processing_pipeline
        self.writer = db_writer if db_writer is not None else (writers[0] if writers else None)
        self.writers = writers if writers is not None else ([self.writer] if self.writer else [])
        self.msg_queue: queue.Queue = queue.Queue(maxsize=10000)
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=pool_workers, thread_name_prefix="iob_worker")
        self.active = False

    def enqueue_raw_packet(self, raw_bytes: bytes) -> None:
        try:
            self.msg_queue.put_nowait(raw_bytes)
        except queue.Full:
            logger.error("Internal processing buffer full. Dropping incoming real-time telemetry metrics.")

    def register_writer(self, writer: IDatabaseWriter) -> None:
        if writer not in self.writers:
            self.writers.append(writer)
        self.writer = writer

    def start(self) -> None:
        self.active = True
        for _ in range(self.pool._max_workers):
            self.pool.submit(self._worker_loop)
        logger.info(f"Dispatcher thread worker pools spun up. Threads spawned: {self.pool._max_workers}")

    def stop(self) -> None:
        self.active = False
        self.pool.shutdown(wait=True)
        logger.info("Dispatcher thread worker pools closed.")

    def _worker_loop(self) -> None:
        while self.active or not self.msg_queue.empty():
            try:
                raw_bytes = self.msg_queue.get(timeout=0.15)
            except queue.Empty:
                if not self.active:
                    break
                continue

            try:
                if self.pipeline:
                    model: Optional[StandardizedTelemetryModel] = self.pipeline.process_raw_message(raw_bytes)
                    if model and self.writer:
                        self.writer.save_telemetry_record(model)
            except Exception as ex:
                logger.error(f"Worker iteration loop error: {str(ex)}")
            finally:
                self.msg_queue.task_done()

    def process(self, payload: Any) -> Any:
        model = payload.get("_model") if isinstance(payload, dict) else payload
        if model and self.writers:
            for w in self.writers:
                w.save_telemetry_record(model)
        return payload


# Backwards compatibility alias
EventDispatcher = TelemetryEventDispatcher
