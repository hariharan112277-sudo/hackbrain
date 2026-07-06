"""
Industrial Operating Brain (IOB): Phase 7 — AI-Ready Data Preparation Pipeline.
"""
from .logger import get_pipeline_logger
from .config import DataPipelineSettings, pipeline_config
from .extractor import IndustrialDataExtractor
from .cleaner import IndustrialDataCleaner
from .transformer import IndustrialDataTransformer
from .aggregator import TimeSeriesAggregator
from .label_generator import IndustrialLabelGenerator
from .statistics import DatasetStatisticsProfiler
from .validator import DatasetIntegrityValidator
from .exporter import DatasetStorageExporter
from .pipeline import PreparationPipelineOrchestrator

__version__ = "7.0.0-DATA"
__all__ = [
    "get_pipeline_logger", "DataPipelineSettings", "pipeline_config",
    "IndustrialDataExtractor", "IndustrialDataCleaner", "IndustrialDataTransformer",
    "TimeSeriesAggregator", "IndustrialLabelGenerator", "DatasetStatisticsProfiler",
    "DatasetIntegrityValidator", "DatasetStorageExporter", "PreparationPipelineOrchestrator"
]
