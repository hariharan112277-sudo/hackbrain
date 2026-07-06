# IOB Process Engineering Features Dictionary (Metadata Specification Manifest)

This reference dictionary profiles every extracted and processed feature in the exported dataset, helping **Member 3 (AI/ML Engineer)** select models without needing further feature conversion.

## Core Time-Series Array Feature Matrices

### 1. measured_value
* **Description:** Cleansed physical sensor metric value resampled onto uniform standard grids.
* **Datatype:** Float64
* **Engineering Unit:** Native metric parameter (e.g., °C, bar, mm/s).
* **Value Range Limits:** Dependent on sensor specification rules (e.g., 0.0 - 150.0).
* **Transformation Applied:** Filtered via Modified Z-Score outlier removal; resampled to 1-minute intervals with linear gap interpolation.
* **Downstream ML Strategy:** Core input signal for anomaly detection models and multivariate regression forecasting.

### 2. rolling_std_15m
* **Description:** Rolling standard deviation computed across a moving 15-minute window.
* **Datatype:** Float64
* **Engineering Unit:** Continuous variance parameter scalar.
* **Value Range Limits:** >= 0.0
* **Transformation Applied:** Computed using the Pandas rolling window aggregation method on clean timeseries values.
* **Downstream ML Strategy:** Predictor feature used to capture changing signal volatility, which often points to mechanical wear or hydraulic cavitation.

### 3. remaining_useful_life_hours
* **Description:** Continuous target label tracking time remaining until the next verified failure event.
* **Datatype:** Float64
* **Engineering Unit:** Hours (h)
* **Value Range Limits:** 0.0 to 720.0 (Capped at a maximum 30-day window limit).
* **Transformation Applied:** Calculated retroactively by computing the time difference between the telemetry log timestamp and the closest entry in the failures ledger.
* **Downstream ML Strategy:** Primary continuous label used for supervised remaining useful life regression modeling.
