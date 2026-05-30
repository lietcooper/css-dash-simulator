from __future__ import annotations

from typing import Any


VALID_GRID_SIZES = {30, 50, 75}
VALID_WELL_LOCATIONS = {"center", "left", "right"}


def validate_config(config: dict[str, Any]) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    porosity = config.get("porosity")
    permeability = config.get("permeability")
    injection_rate = config.get("injection_rate")
    duration_days = config.get("duration_days")
    grid_size = config.get("grid_size")
    well_location = config.get("well_location")

    if porosity is None or not isinstance(porosity, (int, float)):
        errors.append("Porosity is required and must be a number.")
    elif not (0 < porosity < 1):
        errors.append("Porosity must be between 0 and 1.")

    if permeability is None or not isinstance(permeability, (int, float)):
        errors.append("Permeability is required and must be a number.")
    elif permeability <= 0:
        errors.append("Permeability must be positive.")

    if injection_rate is None or not isinstance(injection_rate, (int, float)):
        errors.append("Injection rate is required and must be a number.")
    elif injection_rate <= 0:
        errors.append("Injection rate must be positive.")

    if duration_days is None or not isinstance(duration_days, (int, float)):
        errors.append("Duration is required and must be a number.")
    elif duration_days <= 0:
        errors.append("Duration must be positive.")

    if grid_size is None:
        errors.append("Grid size is required.")
    else:
        try:
            if int(grid_size) not in VALID_GRID_SIZES:
                errors.append("Grid size must be one of 30, 50, or 75.")
        except (TypeError, ValueError):
            errors.append("Grid size must be an integer.")

    if well_location is None or well_location not in VALID_WELL_LOCATIONS:
        errors.append("Well location must be one of: center, left, right.")

    if not errors:
        if injection_rate > 3.0:
            warnings.append("High injection rate may cause large pressure buildup.")
        if permeability < 50:
            warnings.append("Low permeability may limit CO₂ migration.")
        if duration_days > 1000:
            warnings.append("Long duration may produce a large plume radius.")

    return {"errors": errors, "warnings": warnings}
