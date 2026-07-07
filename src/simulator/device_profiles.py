"""
Industrial telemetry value generator.

Implements a basic sinusoidal industrial-process variation model with
bounded Gaussian noise — sufficient for discrete, continuous, and
batch manufacturing profiles while keeping the code small and
deterministic-friendly.
"""
from __future__ import annotations

import math
import random
import time
from typing import Any, Dict, Optional


class TelemetryGenerator:
    """
    Stateless telemetry-value generator.

    Used by ``IndustrialSimulator`` to produce one sample per metric
    per tick.  Honors physical min/max bounds and per-metric noise
    amplitude; supports deterministic seeding via the ``step`` counter.
    """

    @staticmethod
    def generate_metric_value(
        metric_cfg: Dict[str, Any],
        step: float,
        rng: Optional[random.Random] = None,
    ) -> float:
        """
        Generate one bounded, noised telemetry value for the given metric.

        Args:
            metric_cfg: dict with ``min_val``, ``max_val``, optional
                ``noise_amplitude`` and ``data_type``.
            step: monotonically increasing step counter (drives a slow
                sinusoidal modulation so successive samples aren't flat).
            rng: optional ``random.Random`` for deterministic output.
                When ``None``, uses the module-level ``random`` state.

        Returns:
            Rounded float clamped to ``[min_val, max_val]``.
        """
        min_v = float(metric_cfg["min_val"])
        max_v = float(metric_cfg["max_val"])
        noise = float(metric_cfg.get("noise_amplitude", 0.0))
        span = max_v - min_v

        _rng = rng or random

        # Slow sinusoidal process variation — gives the signal a plausible
        # industrial-process drift instead of pure random walk.
        # Amplitude is up to 10% of span; period ~50 steps.
        sine_amp = 0.10 * span
        sine = sine_amp * math.sin(step * 0.125)

        # Mid-range operating point with small wobble
        mid = min_v + 0.5 * span
        wobble = _rng.uniform(-0.02, 0.02) * span

        base_val = mid + sine + wobble
        # Symmetric uniform noise within the configured amplitude
        noise_term = _rng.uniform(-noise, noise)

        final_val = base_val + noise_term
        clamped = max(min_v, min(max_v, final_val))
        return round(clamped, 4)

    @staticmethod
    def make_deterministic_rng(seed: int) -> random.Random:
        """Build a per-device ``random.Random`` for reproducible runs."""
        return random.Random(seed)
