from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def build_time_series_figure(result: dict[str, Any]) -> go.Figure:
    time = result["time"]
    pressure = result["pressure"]
    saturation = result["co2_saturation"]
    plume_radius = result["plume_radius"]

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            "Pressure [MPa]",
            "Average CO₂ Saturation [-]",
            "Plume Radius [m]",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=time,
            y=pressure,
            mode="lines",
            name="Pressure",
            line=dict(color="#dc2626", width=2),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=time,
            y=saturation,
            mode="lines",
            name="CO₂ Saturation",
            line=dict(color="#2563eb", width=2),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=time,
            y=plume_radius,
            mode="lines",
            name="Plume Radius",
            line=dict(color="#059669", width=2),
        ),
        row=3,
        col=1,
    )

    fig.update_xaxes(title_text="Time [days]", row=3, col=1)
    fig.update_yaxes(title_text="MPa", row=1, col=1)
    fig.update_yaxes(title_text="-", row=2, col=1)
    fig.update_yaxes(title_text="m", row=3, col=1)

    fig.update_layout(
        height=520,
        margin=dict(l=50, r=20, t=40, b=40),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(gridcolor="#e5e7eb")
    fig.update_yaxes(gridcolor="#e5e7eb")

    return fig


def build_heatmap_figure(
    result: dict[str, Any], variable: str, time_index: int
) -> go.Figure:
    if variable == "saturation":
        grids = result["saturation_grids"]
        colorscale = "Viridis"
        colorbar_title = "Saturation [-]"
        title_prefix = "CO₂ Saturation Field"
        zmin, zmax = 0.0, 1.0
    else:
        grids = result["pressure_grids"]
        colorscale = "Hot"
        colorbar_title = "Pressure [MPa]"
        title_prefix = "Pressure Field"
        zmin, zmax = None, None

    times = result["time"]
    n = len(grids)
    if n == 0:
        return empty_figure("No grid data available")

    idx = max(0, min(int(time_index), n - 1))
    grid = grids[idx]
    day = times[idx]

    heatmap_kwargs: dict[str, Any] = dict(z=grid, colorscale=colorscale, colorbar=dict(title=colorbar_title))
    if zmin is not None:
        heatmap_kwargs["zmin"] = zmin
    if zmax is not None:
        heatmap_kwargs["zmax"] = zmax

    fig = go.Figure(data=go.Heatmap(**heatmap_kwargs))
    fig.update_layout(
        title=f"{title_prefix} at Day {day:.0f}",
        height=480,
        margin=dict(l=40, r=40, t=60, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(title="X [grid cell]", scaleanchor="y", constrain="domain"),
        yaxis=dict(title="Y [grid cell]", autorange="reversed"),
    )

    return fig


def empty_figure(message: str = "Run a simulation to see results") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text=message,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color="#9ca3af"),
            )
        ],
    )
    return fig
