# IOB AI-Ready Dataset Preparation Pipeline (Phase 7 Specification)

## Architectural Design Overview
This module automates the extraction, cleaning, features transformation, and structural labeling of raw historical manufacturing data. It converts raw timeseries parameters into clean feature arrays, eliminating any need for upstream preprocessing by the AI team.

## Manual for Member 3 (AI/ML Engineer Integration Blueprint)
Generated datasets are exported straight onto configured file networks as flat matrices. You can directly ingest these clean matrices into model training environments:

```python
import pandas as pd

# Load clean timeseries data with statistical rolling features and calculated targets
training_df = pd.read_csv("./data_output/historical.csv", parse_dates=['timestamp'])

# Extract clean features and predictive targets directly
X = training_df[[col for col in training_df.columns if 'rolling_' in col or 'measured_' in col]]
y_rul = training_df['remaining_useful_life_hours']
y_binary = training_df['failure_binary_target']
```

## Running the Data Preparation Pipeline
To run the automated extraction, data cleansing, feature transformation, validation, and export workflow, execute the main entry point:

```bash
python -c "from datasets.pipeline import PreparationPipelineOrchestrator; p = PreparationPipelineOrchestrator('ENGINE_SESSION_HERE'); p.run_execution_sequence('2026-07-01', '2026-07-03')"
```

## Local Verification Testing Strategy
Execute the data cleansing and target label verification test suite using the following command:

```bash
pytest datasets/tests/test_pipeline_stages.py -vv
```

---

### Complete Production Datasets Layout

```text
datasets/
├── README.md
├── historical.csv
├── alarms.csv
├── maintenance.csv
├── failures.csv
├── metadata.json
├── feature_dictionary.md
├── pipeline.py
├── extractor.py
├── cleaner.py
├── transformer.py
├── aggregator.py
├── label_generator.py
├── statistics.py
├── validator.py
├── exporter.py
├── config.py
├── logger.py
├── config/
│   ├── dataset.yaml
│   ├── features.yaml
│   ├── labels.yaml
│   └── quality_rules.yaml
├── docs/
└── tests/
    └── test_pipeline_stages.py
```
