"""
Telemetry Processing Pipeline Stage for Industrial Operating Brain (IOB) Phase 4.
Standard Compliance: Linear In-Memory Validation Chain.
"""

import queue
import concurrent.futures
import logging
from typing import Union, Optional, Any
from .config import PipelineConfigManager
from .validator import JsonPayloadValidator
from .timestamp_validator import ChronoTimestampValidator
from .duplicate_detector import SlidingWindowDuplicateDetector
from .quality_checker import OperationalQualityChecker
from .normalizer import EngineeringUnitNormalizer
from .metadata_enricher import StaticAssetMetadataEnricher
from .parser import TelemetryObjectParser
from .models import StandardizedTelemetryModel, RawTelemetryMessage
from .exceptions import IngestionPipelineException, DuplicatePacketException

logger = logging.getLogger("iob.pipeline")


class TelemetryProcessingPipeline:
    """Orchestrates sequential validation, correction, and parsing execution chains."""
    def __init__(self, cfg: Optional[PipelineConfigManager] = None, buffer_queue: Optional[queue.Queue] = None, max_workers: int = 4):
        if cfg is None:
            cfg = PipelineConfigManager()
            cfg.parse_all()
        self.cfg = cfg
        self.buffer_queue = buffer_queue if buffer_queue is not None else queue.Queue(maxsize=10000)
        self.max_workers = max_workers
        self.processed_count = 0
        self.dispatcher: Any = None
        self.active = False
        self.pool: Optional[concurrent.futures.ThreadPoolExecutor] = None

        # 1. Initialize structural components
        self.validator = JsonPayloadValidator(
            cfg.schema,
            cfg.rules.get("validation_parameters", {}).get("max_payload_size_bytes", 1048576)
        )
        self.chrono = ChronoTimestampValidator(
            cfg.rules.get("validation_parameters", {}).get("allowed_clock_drift_future_sec", 5.0),
            cfg.rules.get("validation_parameters", {}).get("allowed_clock_drift_past_sec", 86400.0)
        )
        self.dedup = SlidingWindowDuplicateDetector(
            cfg.rules.get("validation_parameters", {}).get("duplicate_detection_window_sec", 60.0),
            cfg.rules.get("validation_parameters", {}).get("duplicate_cache_max_elements", 50000)
        )
        self.quality = OperationalQualityChecker(cfg.rules.get("quality_rules", {}))
        self.normalizer = EngineeringUnitNormalizer(cfg.units.get("unit_normalization_matrix", {}))
        self.enricher = StaticAssetMetadataEnricher()

    def get_dispatcher(self) -> Any:
        if self.dispatcher is None:
            from .dispatcher import TelemetryEventDispatcher
            from .interfaces import InMemoryDatabaseWriter
            self.dispatcher = TelemetryEventDispatcher(self, InMemoryDatabaseWriter())
        return self.dispatcher

    def process_raw_message(self, raw_bytes: Union[bytes, str, RawTelemetryMessage]) -> Optional[StandardizedTelemetryModel]:
        if isinstance(raw_bytes, RawTelemetryMessage):
            raw_bytes = raw_bytes.payload
        if isinstance(raw_bytes, str):
            raw_bytes = raw_bytes.encode("utf-8")

        try:
            # Stage 1: Structural syntax verification
            payload = self.validator.execute_validation(raw_bytes)

            # Stage 2: Chrono clock accuracy checks
            self.chrono.assert_timestamp_bounds(payload)

            # Stage 3: Sliding window duplicate filtration checks
            if self.dedup.process_deduplication_check(payload):
                raise DuplicatePacketException(f"Duplicate sequence discarded: {payload.get('sensor_id')} #{payload.get('sequence_number')}")

            # Stage 4: Process operations validation checks
            score = self.quality.evaluate_quality_score(payload)

            # Stage 5: Engineering scaling conversions
            self.normalizer.normalize_inplace(payload)

            # Stage 6: Structural metadata injection
            self.enricher.enrich_envelope(payload, score)

            self.processed_count += 1
            # Stage 7: Strongly typed mapping transformation
            model = TelemetryObjectParser.map_to_frozen_model(payload)
            if self.dispatcher and hasattr(self.dispatcher, "writers") and self.dispatcher.writers:
                for w in self.dispatcher.writers:
                    w.save_telemetry_record(model)
            elif self.dispatcher and hasattr(self.dispatcher, "writer") and self.dispatcher.writer:
                self.dispatcher.writer.save_telemetry_record(model)
            return model

        except DuplicatePacketException as ex:
            logger.debug(str(ex))
            return None
        except IngestionPipelineException as ex:
            logger.error(f"Pipeline processing error: {str(ex)}", extra={"context": {"raw_size": len(raw_bytes)}})
            return None
        except Exception as ex:
            logger.critical(f"Unhandled critical system processing exception: {str(ex)}", exc_info=True)
            return None

    def _worker_loop(self) -> None:
        while self.active or not self.buffer_queue.empty():
            try:
                raw_bytes = self.buffer_queue.get(timeout=0.1)
            except queue.Empty:
                if not self.active:
                    break
                continue
            try:
                self.process_raw_message(raw_bytes)
            finally:
                self.buffer_queue.task_done()

    def start(self) -> None:
        self.active = True
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="iob_pipeline_worker")
        for _ in range(self.max_workers):
            self.pool.submit(self._worker_loop)

    def stop(self) -> None:
        self.active = False
        if self.pool:
            self.pool.shutdown(wait=True)
