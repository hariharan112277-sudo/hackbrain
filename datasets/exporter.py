"""
Thread-Safe Output Exporter Interface Strategy.
"""
import os
import json
import pandas as pd
from datasets.logger import get_pipeline_logger
from datasets.config import pipeline_config

logger = get_pipeline_logger("exporter")


class DatasetStorageExporter:
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or pipeline_config.OUTPUT_BASE_DIR
        os.makedirs(self.base_dir, exist_ok=True)

    def save_dataframe_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """Persists structural pandas matrices directly out onto disk networks."""
        target_path = os.path.join(self.base_dir, filename)
        logger.info(f"Writing dataset file array layer downstream onto local storage fields: {target_path}")
        df.to_csv(target_path, index=False)
        return target_path

    def save_metadata_manifest_json(self, metadata: dict, filename: str) -> str:
        """Serializes integration tracking runtime indicators directly onto active target zones."""
        target_path = os.path.join(self.base_dir, filename)
        logger.info(f"Exporting operational workflow metrics onto JSON file paths: {target_path}")
        with open(target_path, 'w', encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
        return target_path

    def save_text_content(self, content: str, filename: str) -> str:
        target_path = os.path.join(self.base_dir, filename)
        with open(target_path, 'w', encoding="utf-8") as f:
            f.write(content)
        return target_path
