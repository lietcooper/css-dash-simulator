from __future__ import annotations

import json
import time
import uuid
from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dash_table, dcc, html

from src.figures import build_heatmap_figure, build_time_series_figure, empty_figure
from src.postprocess import summary_to_dataframe, time_series_dataframe
from src.simulator import run_mock_ccs_simulation
from src.validation import validate_config


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="CCS Simulation Dashboard",
    suppress_callback_exceptions=False,
)
server = app.server


GRID_OPTIONS = [
    {"label": "30 x 30", "value": 30},
    {"label": "50 x 50", "value": 50},
    {"label": "75 x 75", "value": 75},
]

WELL_OPTIONS = [
    {"label": "Center", "value": "center"},
    {"label": "Left", "value": "left"},
    {"label": "Right", "value": "right"},
]

VARIABLE_OPTIONS = [
    {"label": "Pressure", "value": "pressure"},
    {"label": "CO₂ Saturation", "value": "saturation"},
]

SCENARIO_COLUMNS = [
    {"name": "Run ID", "id": "run_id"},
    {"name": "Porosity", "id": "porosity"},
    {"name": "Permeability [mD]", "id": "permeability_mD"},
    {"name": "Injection Rate [Mt/yr]", "id": "injection_rate_Mt_yr"},
    {"name": "Duration [days]", "id": "duration_days"},
    {"name": "Max Pressure [MPa]", "id": "max_pressure_MPa"},
    {"name": "Final Saturation", "id": "final_avg_saturation"},
    {"name": "Max Plume [m]", "id": "max_plume_radius_m"},
    {"name": "Stored CO₂ [Mt]", "id": "total_stored_co2_Mt"},
]


def _labeled(label: str, control: Any, hint: str | None = None) -> html.Div:
    children = [dbc.Label(label, className="input-label")]
    children.append(control)
    if hint:
        children.append(html.Div(hint, className="input-hint"))
    return html.Div(children, className="input-row")


def _slider_marks(min_v: float, max_v: float, n: int = 5) -> dict:
    step = (max_v - min_v) / (n - 1)
    marks = {}
    for i in range(n):
        v = min_v + step * i
        if float(v).is_integer():
            marks[int(v)] = str(int(v))
        else:
            marks[round(v, 2)] = f"{v:.2f}"
    return marks


def _input_panel() -> dbc.Card:
    return dbc.Card(
        [
            html.Div("Simulation Inputs", className="card-title"),
            _labeled(
                "Porosity [-]",
                dcc.Slider(
                    id="in-porosity",
                    min=0.05,
                    max=0.40,
                    step=0.01,
                    value=0.22,
                    marks=_slider_marks(0.05, 0.40, 5),
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ),
            _labeled(
                "Permeability [mD]",
                dcc.Slider(
                    id="in-permeability",
                    min=10,
                    max=1000,
                    step=10,
                    value=150,
                    marks=_slider_marks(10, 1000, 5),
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ),
            _labeled(
                "Injection Rate [Mt/year]",
                dcc.Slider(
                    id="in-injection-rate",
                    min=0.1,
                    max=5.0,
                    step=0.1,
                    value=1.5,
                    marks=_slider_marks(0.1, 5.0, 5),
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ),
            _labeled(
                "Duration [days]",
                dcc.Slider(
                    id="in-duration",
                    min=30,
                    max=2000,
                    step=10,
                    value=365,
                    marks=_slider_marks(30, 2000, 5),
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ),
            _labeled(
                "Grid Size",
                dcc.Dropdown(
                    id="in-grid-size",
                    options=GRID_OPTIONS,
                    value=50,
                    clearable=False,
                ),
            ),
            _labeled(
                "Well Location",
                dcc.Dropdown(
                    id="in-well-location",
                    options=WELL_OPTIONS,
                    value="center",
                    clearable=False,
                ),
            ),
            _labeled(
                "Random Seed",
                dcc.Input(
                    id="in-random-seed",
                    type="number",
                    value=42,
                    step=1,
                    style={"width": "100%"},
                ),
            ),
            dbc.Button(
                "Run Simulation",
                id="run-btn",
                color="primary",
                className="run-button",
                n_clicks=0,
            ),
            html.Div(id="validation-msg", style={"marginTop": "12px"}),
        ],
        className="card",
        body=False,
    )


def _summary_panel() -> dbc.Card:
    def _metric_row(label: str, value_id: str) -> html.Div:
        return html.Div(
            [
                html.Span(label, className="metric-label"),
                html.Span("—", id=value_id, className="metric-value"),
            ],
            className="metric",
        )

    return dbc.Card(
        [
            html.Div(
                [
                    html.Span("Run Summary", className="card-title"),
                    dbc.Badge(
                        "Ready",
                        id="status-badge",
                        color="secondary",
                        className="ms-2",
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
            ),
            _metric_row("Run ID", "summary-run-id"),
            _metric_row("Max Pressure [MPa]", "summary-max-pressure"),
            _metric_row("Final Avg Saturation [-]", "summary-final-sat"),
            _metric_row("Max Plume Radius [m]", "summary-max-plume"),
            _metric_row("Stored CO₂ [Mt]", "summary-stored-co2"),
            _metric_row("Warnings", "summary-warnings"),
        ],
        className="card",
        body=False,
    )


def _tabs_section() -> dbc.Card:
    time_series_tab = dbc.Tab(
        dcc.Graph(
            id="time-series-graph",
            figure=empty_figure("Run a simulation to see time-series"),
        ),
        label="Time Series",
        tab_id="tab-ts",
    )

    heatmap_controls = dbc.Row(
        [
            dbc.Col(
                _labeled(
                    "Output Variable",
                    dcc.Dropdown(
                        id="heatmap-variable",
                        options=VARIABLE_OPTIONS,
                        value="pressure",
                        clearable=False,
                    ),
                ),
                width=4,
            ),
            dbc.Col(
                _labeled(
                    "Time Step",
                    dcc.Slider(
                        id="time-slider",
                        min=0,
                        max=79,
                        step=1,
                        value=40,
                        marks={0: "0", 20: "20", 40: "40", 60: "60", 79: "79"},
                        tooltip={"placement": "bottom", "always_visible": True},
                        disabled=True,
                    ),
                ),
                width=8,
            ),
        ],
        className="g-2",
    )

    heatmap_tab = dbc.Tab(
        html.Div(
            [
                heatmap_controls,
                dcc.Graph(
                    id="heatmap-graph",
                    figure=empty_figure("Run a simulation to see heatmap"),
                ),
            ]
        ),
        label="Spatial Heatmap",
        tab_id="tab-heatmap",
    )

    scenario_tab = dbc.Tab(
        html.Div(
            [
                dash_table.DataTable(
                    id="scenario-table",
                    columns=SCENARIO_COLUMNS,
                    data=[],
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "fontFamily": "Arial, sans-serif",
                        "fontSize": "13px",
                        "padding": "8px",
                        "textAlign": "left",
                    },
                    style_header={
                        "fontWeight": "600",
                        "backgroundColor": "#f3f4f6",
                        "color": "#111827",
                    },
                    page_size=10,
                ),
            ]
        ),
        label="Scenario Data",
        tab_id="tab-scenarios",
    )

    return dbc.Card(
        [
            dbc.Tabs(
                [time_series_tab, heatmap_tab, scenario_tab],
                id="tabs",
                active_tab="tab-ts",
            ),
        ],
        className="card",
        body=True,
    )


def _export_row() -> html.Div:
    return html.Div(
        [
            dbc.Button(
                "Download CSV",
                id="dl-csv-btn",
                color="secondary",
                outline=True,
                className="me-2",
            ),
            dbc.Button(
                "Download JSON",
                id="dl-json-btn",
                color="secondary",
                outline=True,
            ),
            dcc.Download(id="dl-csv"),
            dcc.Download(id="dl-json"),
        ],
        style={"marginBottom": "24px"},
    )


app.layout = html.Div(
    [
        html.Div(
            [
                html.H1("CCS Simulation Dashboard", className="page-title"),
                html.Div(
                    "Configure, run, and visualize simplified CO₂ storage",
                    className="page-subtitle",
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(_input_panel(), md=4, sm=12),
                dbc.Col(_summary_panel(), md=8, sm=12),
            ],
            className="g-3",
        ),
        _tabs_section(),
        _export_row(),
        dcc.Store(id="current-result"),
        dcc.Store(id="runs-history", data=[]),
    ],
    className="page",
)


def _format_number(value: Any, fmt: str = "{:.3f}") -> str:
    try:
        return fmt.format(float(value))
    except (TypeError, ValueError):
        return "—"


def _status_badge_props(status: str) -> tuple[str, str]:
    mapping = {
        "Ready": ("Ready", "secondary"),
        "Running": ("Running", "warning"),
        "Completed": ("Completed", "success"),
        "Validation failed": ("Validation failed", "danger"),
        "Error": ("Error", "danger"),
    }
    return mapping.get(status, (status, "secondary"))


@app.callback(
    Output("current-result", "data"),
    Output("runs-history", "data"),
    Output("validation-msg", "children"),
    Output("status-badge", "children"),
    Output("status-badge", "color"),
    Output("summary-run-id", "children"),
    Output("summary-max-pressure", "children"),
    Output("summary-final-sat", "children"),
    Output("summary-max-plume", "children"),
    Output("summary-stored-co2", "children"),
    Output("summary-warnings", "children"),
    Output("time-series-graph", "figure"),
    Output("scenario-table", "data"),
    Output("time-slider", "disabled"),
    Input("run-btn", "n_clicks"),
    State("in-porosity", "value"),
    State("in-permeability", "value"),
    State("in-injection-rate", "value"),
    State("in-duration", "value"),
    State("in-grid-size", "value"),
    State("in-well-location", "value"),
    State("in-random-seed", "value"),
    State("runs-history", "data"),
    prevent_initial_call=True,
)
def on_run_simulation(
    n_clicks: int,
    porosity: float,
    permeability: float,
    injection_rate: float,
    duration_days: float,
    grid_size: int,
    well_location: str,
    random_seed: int,
    runs_history: list[dict],
) -> tuple:
    runs_history = runs_history or []
    config: dict[str, Any] = {
        "porosity": porosity,
        "permeability": permeability,
        "injection_rate": injection_rate,
        "duration_days": int(duration_days) if duration_days is not None else duration_days,
        "grid_size": grid_size,
        "well_location": well_location,
        "random_seed": int(random_seed) if random_seed is not None else 42,
    }

    validation = validate_config(config)
    errors = validation["errors"]
    warnings = validation["warnings"]

    if errors:
        msg = html.Div(
            [html.Div(f"• {e}", className="error-text") for e in errors]
        )
        label, color = _status_badge_props("Validation failed")
        return (
            dash.no_update,
            dash.no_update,
            msg,
            label,
            color,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    warning_children: list = []
    if warnings:
        warning_children = [html.Div(f"• {w}", className="warning-text") for w in warnings]

    try:
        result = run_mock_ccs_simulation(config)
    except Exception as exc:  # noqa: BLE001
        label, color = _status_badge_props("Error")
        msg = html.Div(
            warning_children
            + [html.Div(f"Simulation failed: {exc}", className="error-text")]
        )
        return (
            dash.no_update,
            dash.no_update,
            msg,
            label,
            color,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    run_id = f"run-{int(time.time())}-{uuid.uuid4().hex[:6]}"

    summary = result.get("summary", {})
    summary_df = summary_to_dataframe(result, run_id, config)
    new_row = summary_df.to_dict("records")[0]
    updated_history = runs_history + [new_row]

    ts_fig = build_time_series_figure(result)

    label, color = _status_badge_props("Completed")
    warnings_text = "; ".join(warnings) if warnings else "None"

    validation_msg = html.Div(warning_children) if warning_children else ""

    return (
        result,
        updated_history,
        validation_msg,
        label,
        color,
        run_id,
        _format_number(summary.get("max_pressure"), "{:.2f}"),
        _format_number(summary.get("final_avg_saturation"), "{:.3f}"),
        _format_number(summary.get("max_plume_radius"), "{:.1f}"),
        _format_number(summary.get("total_stored_co2"), "{:.3f}"),
        warnings_text,
        ts_fig,
        updated_history,
        False,
    )


@app.callback(
    Output("heatmap-graph", "figure"),
    Input("time-slider", "value"),
    Input("heatmap-variable", "value"),
    State("current-result", "data"),
)
def on_update_heatmap(
    time_index: int, variable: str, data: dict | None
) -> Any:
    if not data:
        return empty_figure("Run a simulation to see heatmap")
    try:
        return build_heatmap_figure(data, variable or "pressure", int(time_index or 0))
    except Exception as exc:  # noqa: BLE001
        return empty_figure(f"Could not render heatmap: {exc}")


@app.callback(
    Output("dl-csv", "data"),
    Input("dl-csv-btn", "n_clicks"),
    State("current-result", "data"),
    prevent_initial_call=True,
)
def on_download_csv(n_clicks: int, data: dict | None) -> Any:
    if not data:
        raise dash.exceptions.PreventUpdate
    df = time_series_dataframe(data)
    return dcc.send_data_frame(df.to_csv, "ccs_timeseries.csv", index=False)


@app.callback(
    Output("dl-json", "data"),
    Input("dl-json-btn", "n_clicks"),
    State("current-result", "data"),
    prevent_initial_call=True,
)
def on_download_json(n_clicks: int, data: dict | None) -> Any:
    if not data:
        raise dash.exceptions.PreventUpdate
    payload = {
        "config": data.get("config", {}),
        "summary": data.get("summary", {}),
        "warnings": data.get("warnings", []),
    }
    return dict(content=json.dumps(payload, indent=2), filename="ccs_run.json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
