from __future__ import annotations

import numpy as np
import pandas as pd


FEATURES = ["stride_length", "step_height", "swing_duration", "asymmetry", "joint_angle_range", "velocity"]


def make_synthetic_longitudinal_tbi(
    n_animals_per_condition: int = 12, sessions_per_timepoint: int = 3, seed: int = 7
) -> pd.DataFrame:
    """Create a labelled demonstration cohort, never experimental evidence.

    TBI animals include a mixture of 10-day restitution, compensation, and
    persistent dysfunction patterns. Repeated observations deliberately share
    animal baselines to exercise leakage-safe analysis.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    timepoints = [("baseline", 0), ("day_1", 1), ("day_10", 10)]
    for condition in ("sham", "tbi"):
        for index in range(n_animals_per_condition):
            animal = f"{condition.upper()}_{index + 1:02d}"
            baseline = rng.normal(0, 0.6, len(FEATURES))
            recovery_type = "sham" if condition == "sham" else ["restitution", "compensation", "persistent_dysfunction"][index % 3]
            for timepoint, day in timepoints:
                if condition == "sham" or timepoint == "baseline":
                    shift = np.zeros(len(FEATURES))
                    performance_shift = 0.0
                elif timepoint == "day_1":
                    shift = np.array([-1.2, -1.0, 0.8, 1.2, -1.0, -0.8])
                    performance_shift = -0.45
                elif recovery_type == "restitution":
                    shift, performance_shift = np.array([-0.1, -0.1, 0.05, 0.1, -0.1, -0.05]), -0.02
                elif recovery_type == "compensation":
                    shift, performance_shift = np.array([0.6, -0.7, 0.55, 0.9, -0.65, 0.05]), -0.03
                else:
                    shift, performance_shift = np.array([-0.8, -0.8, 0.7, 1.0, -0.7, -0.5]), -0.35
                for session in range(sessions_per_timepoint):
                    values = baseline + shift + rng.normal(0, 0.18, len(FEATURES))
                    row = dict(zip(FEATURES, values, strict=True))
                    row.update({
                        "dataset_id": "synthetic_tbi", "animal_id": animal,
                        "session_id": f"{animal}_{timepoint}_{session:02d}", "timepoint": timepoint,
                        "days_post_injury": day, "condition": condition, "injury_status": condition,
                        "task_success": float(np.clip(0.93 + performance_shift + rng.normal(0, 0.035), 0, 1)),
                        "tracking_quality": float(np.clip(rng.normal(0.96, 0.025), 0.75, 1)),
                        "is_synthetic": True, "recovery_pattern": recovery_type,
                    })
                    rows.append(row)
    return pd.DataFrame(rows)
