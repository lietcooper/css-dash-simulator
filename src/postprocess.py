from __future__ import annotations

from typing import Any

import pandas as pd


def time_series_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time_days": result["time"],
            "pressure_mpa": result["pressure"],
            "co2_saturation": result["co2_saturation"],
            "plume_radius_m": result["plume_radius"],
            "stored_co2_mt": result["stored_co2_mass"],
        }
    )


def summary_to_dataframe(
    result: dict[str, Any], run_id: str, config: dict[str, Any]
) -> pd.DataFrame:
    summary = result.get("summary", {})
    warnings = result.get("warnings", []) or []
    row = {
        "run_id": run_id,
        "porosity": config.get("porosity"),
        "permeability_mD": config.get("permeability"),
        "injection_rate_Mt_yr": config.get("injection_rate"),
        "duration_days": config.get("duration_days"),
        "grid_size": config.get("grid_size"),
        "well_location": config.get("well_location"),
        "max_pressure_MPa": summary.get("max_pressure"),
        "final_avg_saturation": summary.get("final_avg_saturation"),
        "max_plume_radius_m": summary.get("max_plume_radius"),
        "total_stored_co2_Mt": summary.get("total_stored_co2"),
        "warnings": "; ".join(warnings) if warnings else "",
    }
    return pd.DataFrame([row])
