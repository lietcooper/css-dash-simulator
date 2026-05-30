from __future__ import annotations

import time as _time
from typing import Any

import numpy as np


INITIAL_PRESSURE_MPA = 12.0
PRESSURE_SCALE_CONST = 80.0
PRESSURE_TAU_FRACTION = 0.35
MAX_SATURATION = 0.7
SAT_TAU_FRACTION = 0.4
PLUME_SCALE_CONST = 8.0


def _well_indices(grid_size: int, well_location: str) -> tuple[int, int]:
    if well_location == "left":
        cx = int(grid_size * 0.25)
    elif well_location == "right":
        cx = int(grid_size * 0.75)
    else:
        cx = grid_size // 2
    cy = grid_size // 2
    return cx, cy


def run_mock_ccs_simulation(config: dict[str, Any]) -> dict[str, Any]:
    porosity = float(config["porosity"])
    permeability = float(config["permeability"])
    injection_rate = float(config["injection_rate"])
    duration_days = float(config["duration_days"])
    grid_size = int(config["grid_size"])
    well_location = str(config["well_location"])
    random_seed = int(config.get("random_seed", 42))

    rng = np.random.default_rng(random_seed)

    time = np.linspace(0.0, duration_days, num=80)

    pressure_scale = PRESSURE_SCALE_CONST * injection_rate / np.sqrt(permeability)
    tau_p = max(PRESSURE_TAU_FRACTION * duration_days, 1.0)
    pressure = INITIAL_PRESSURE_MPA + pressure_scale * (1.0 - np.exp(-time / tau_p))
    pressure = pressure + rng.normal(0.0, 0.05, size=pressure.shape)

    tau_sat = max(SAT_TAU_FRACTION * duration_days, 1.0)
    saturation = MAX_SATURATION * (1.0 - np.exp(-time / tau_sat))
    saturation = np.clip(saturation + rng.normal(0.0, 0.005, size=saturation.shape), 0.0, 1.0)

    plume_radius = PLUME_SCALE_CONST * np.sqrt(np.maximum(injection_rate * time, 0.0) / porosity)

    stored_co2_mass = injection_rate * time / 365.0

    cx, cy = _well_indices(grid_size, well_location)
    yy, xx = np.meshgrid(np.arange(grid_size), np.arange(grid_size), indexing="ij")
    distance_sq = (xx - cx) ** 2 + (yy - cy) ** 2

    pressure_amp_base = pressure_scale
    saturation_amp_base = MAX_SATURATION

    base_spread = max(grid_size * 0.05, 1.5)
    spread_growth = grid_size * 0.35

    pressure_grids: list[list[list[float]]] = []
    saturation_grids: list[list[list[float]]] = []

    duration_safe = max(duration_days, 1.0)

    for i, t in enumerate(time):
        progress = t / duration_safe
        spread = base_spread + spread_growth * np.sqrt(progress)
        spread_sq = max(spread * spread, 1.0)

        p_amp = pressure_amp_base * (1.0 - np.exp(-t / tau_p))
        p_field = INITIAL_PRESSURE_MPA + p_amp * np.exp(-distance_sq / (2.0 * spread_sq))
        p_field = p_field + rng.normal(0.0, 0.02, size=p_field.shape)

        s_amp = saturation_amp_base * (1.0 - np.exp(-t / tau_sat))
        s_field = s_amp * np.exp(-distance_sq / (2.0 * spread_sq))
        s_field = np.clip(s_field + rng.normal(0.0, 0.005, size=s_field.shape), 0.0, 1.0)

        pressure_grids.append(p_field.tolist())
        saturation_grids.append(s_field.tolist())

    summary = {
        "max_pressure": float(np.max(pressure)),
        "final_avg_saturation": float(saturation[-1]),
        "max_plume_radius": float(np.max(plume_radius)),
        "total_stored_co2": float(stored_co2_mass[-1]),
        "duration_days": float(duration_days),
    }

    _time.sleep(0.5)

    return {
        "time": time.tolist(),
        "pressure": pressure.tolist(),
        "co2_saturation": saturation.tolist(),
        "plume_radius": plume_radius.tolist(),
        "stored_co2_mass": stored_co2_mass.tolist(),
        "pressure_grids": pressure_grids,
        "saturation_grids": saturation_grids,
        "summary": summary,
        "warnings": [],
        "config": {
            "porosity": porosity,
            "permeability": permeability,
            "injection_rate": injection_rate,
            "duration_days": duration_days,
            "grid_size": grid_size,
            "well_location": well_location,
            "random_seed": random_seed,
        },
    }
