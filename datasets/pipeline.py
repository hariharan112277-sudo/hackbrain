"""
Unified Orchestrator Workflow Pipeline Manager Core Module Engine.
"""
import os
from datetime import datetime, timezone
from typing import Any, Dict
from datasets.logger import get_pipeline_logger
from datasets.config import pipeline_config
from datasets.extractor import IndustrialDataExtractor
from datasets.cleaner import IndustrialDataCleaner
from datasets.transformer import IndustrialDataTransformer
from datasets.aggregator import TimeSeriesAggregator
from datasets.label_generator import IndustrialLabelGenerator
from datasets.statistics import DatasetStatisticsProfiler
from datasets.validator import DatasetIntegrityValidator
from datasets.exporter import DatasetStorageExporter

logger = get_pipeline_logger("pipeline")


class PreparationPipelineOrchestrator:
    def __init__(self, db_session_handle: Any, output_dir: str = None):
        self.extractor = IndustrialDataExtractor(db_session_handle)
        self.cleaner = IndustrialDataCleaner()
        self.transformer = IndustrialDataTransformer()
        self.aggregator = TimeSeriesAggregator()
        self.labeler = IndustrialLabelGenerator()
        self.exporter = DatasetStorageExporter(base_dir=output_dir)

    def run_execution_sequence(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Executes the extraction, feature computation, labeling, validation, and export workflow."""
        logger.info("Initializing Dataset Preparation Pipeline workflow sequence...")

        # 1. Extraction
        raw_telemetry = self.extractor.extract_telemetry_window(start_time, end_time)
        raw_failures = self.extractor.extract_failures_ledger()
        raw_alarms = self.extractor.extract_alarm_history()
        raw_maintenance = self.extractor.extract_maintenance_logs()

        # 2. Cleaning & Temporal Grid Standardization
        cleaned_telemetry = self.cleaner.purge_and_realign_telemetry(raw_telemetry)

        # 3. Structural Processing & Feature Transformations
        normalized_telemetry = self.transformer.normalize_engineering_units(cleaned_telemetry)
        encoded_telemetry = self.transformer.transform_categorical_states(normalized_telemetry)

        # 4. Multi-Window Statistical Resampling Feature Accumulations
        feature_matrix = self.aggregator.calculate_rolling_features(encoded_telemetry)

        # 5. Continuous & Binary Target Label Generation
        final_labeled_dataset = self.labeler.append_predictive_maintenance_labels(feature_matrix, raw_failures)

        # 6. Data Validation and Compliance Profiling
        schema_rules = ['timestamp', 'machine_id', 'sensor_id', 'measured_value', 'failure_binary_target']
        validation_report = DatasetIntegrityValidator.validate_dataset_schema(final_labeled_dataset, schema_rules)
        statistical_profile = DatasetStatisticsProfiler.generate_comprehensive_profile(final_labeled_dataset)

        # 7. Write Structured Datasets onto Local Media Arrays
        self.exporter.save_dataframe_to_csv(final_labeled_dataset, "historical.csv")
        self.exporter.save_dataframe_to_csv(raw_failures, "failures.csv")
        self.exporter.save_dataframe_to_csv(raw_alarms, "alarms.csv")
        self.exporter.save_dataframe_to_csv(raw_maintenance, "maintenance.csv")

        # Copy feature dictionary specification to output dir
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dict_path = os.path.join(base_dir, "feature_dictionary.md")
        if os.path.exists(dict_path):
            with open(dict_path, "r", encoding="utf-8") as f:
                self.exporter.save_text_content(f.read(), "feature_dictionary.md")

        # Compile and export runtime properties metadata manifest parameters
        metadata_manifest = {
            "pipeline_run_version": pipeline_config.DATASET_VERSION,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_results_summary": validation_report,
            "statistical_profile_metrics": statistical_profile
        }
        self.exporter.save_metadata_manifest_json(metadata_manifest, "metadata.json")

        logger.info("Pipeline executed successfully. Outputs exported and ready for Member 3.")
        return metadata_manifest
