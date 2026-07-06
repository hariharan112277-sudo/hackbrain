"""
IOB Phase 3 - Physics Waveform Engine

Advanced mathematical physics engine computing thermodynamic curves,
sinusoidal drift, load scaling, and deterministic sensor responses.
"""

import math
import random
from typing import Tuple


class PhysicsWaveformEngine:
    """
    Advanced mathematical physics engine computing thermodynamic curves,
    sinusoidal drift, load scaling, and deterministic sensor responses.
    """

    # State Modifier Coefficients Matrix
    STATE_MULTIPLIER = {
        "OFF": 0.0,
        "STARTING": 0.3,
        "RUNNING": 1.0,
        "IDLE": 0.15,
        "WARNING": 1.25,
        "ALARM": 1.45,
        "STOPPING": 0.4,
        "MAINTENANCE": 0.05,
        "FAULT": 0.0,
        "EMERGENCY_STOP": 0.0,
    }

    # De-energised / fault states collapse output to a hard zero, or to the
    # sensor's ambient reference base point (Emergency-Stop signature, spec 6).
    ZERO_OUTPUT_STATES = frozenset({"OFF", "FAULT", "EMERGENCY_STOP"})

    @staticmethod
    def compute_next_value(
        state: str,
        base_val: float,
        elapsed_time: float,
        noise_var: float,
        drift_acc: float,
        limits: Tuple[float, float],
    ) -> Tuple[float, str]:
        """
        Executes physical state matrix transformation for individual telemetry tracks.
        """
        min_limit, max_limit = limits

        if state in PhysicsWaveformEngine.ZERO_OUTPUT_STATES:
            # Immediate step response: drop to zero, or to the sensor's
            # environmental ambient reference base point when its lower range
            # sits above zero (e.g. a temperature probe whose floor is 20 C).
            target_value = min_limit if min_limit > 0.0 else 0.0
            quality = "GOOD"
        else:
            # 1. State Modifier Coefficients Matrix
            state_multiplier = PhysicsWaveformEngine.STATE_MULTIPLIER.get(state, 1.0)

            # 2. Synthesis of Waveform Components
            # Periodic Oscillation
            oscillation = math.sin(elapsed_time * 0.05) * (base_val * 0.02)

            # Gaussian Noise Generation (Box-Muller Transform)
            u1 = random.random()
            u2 = random.random()
            noise = (
                math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2) * noise_var
            )

            # Compute targeted absolute output scalar
            target_value = (base_val * state_multiplier) + oscillation + noise + drift_acc

            # Thermal inertia emulation for starting phase
            if state == "STARTING":
                target_value = (base_val * 0.5) + (base_val * 0.4 * math.sin(elapsed_time * 0.2))

            quality = "GOOD"

        # 3. Dynamic Boundary Clamping and Guarding
        if target_value > max_limit:
            target_value = max_limit
            quality = "LIMIT_CLAMPED"
        elif target_value < min_limit:
            target_value = min_limit
            quality = "LIMIT_CLAMPED"

        return round(target_value, 4), quality
