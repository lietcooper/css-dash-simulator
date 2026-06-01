# Dash + Plotly CCS Simulation Dashboard Demo Plan

## 1. Demo 目标

Build a Python-based Dash + Plotly web dashboard that simulates a simplified Carbon Capture and Storage workflow.

The demo should allow users to:

1. Configure simulation parameters.
2. Run a mock CCS simulation.
3. View execution status.
4. Explore simulation outputs through interactive Plotly charts.
5. Compare basic results.
6. Export results as CSV / JSON if feasible.
7. Run locally and optionally through Docker.

The purpose is not to build a scientifically accurate CCS simulator. The purpose is to demonstrate software engineering workflow for wrapping scientific Python computation into a usable web tool.

---

# 2. Tech Stack

Use:

```text
Python 3.11+
Dash
Plotly
pandas
numpy
dash-bootstrap-components, optional but recommended
```

Optional:

```text
Docker
pytest
```

Do not use React or FastAPI in this first version. This should be a pure Dash + Plotly demo.

---

# 3. Recommended Project Structure

```text
ccs-dash-demo/
├── app.py
├── requirements.txt
├── README.md
├── Dockerfile
├── data/
│   └── sample_runs/
├── src/
│   ├── __init__.py
│   ├── simulator.py
│   ├── postprocess.py
│   ├── figures.py
│   └── validation.py
└── assets/
    └── style.css
```

Explanation:

```text
app.py              Dash layout and callbacks
simulator.py        mock CCS simulation logic
postprocess.py      convert raw arrays into pandas DataFrames and summaries
figures.py          Plotly figure generation
validation.py       validate user input ranges
assets/style.css    optional custom styling
```

Keep the code modular. The interview story should be: “I separated UI, simulation logic, post-processing, validation, and visualization.”

---

# 4. Dashboard Layout

Create a single-page dashboard titled:

```text
CCS Simulation Dashboard
```

Use a two-column layout:

```text
Left Panel: Simulation Inputs
Right Panel: Run Summary

Bottom Section:
- Time-series charts
- 2D heatmap with time slider
- Scenario/result table
- Export buttons if feasible
```

Suggested visual layout:

```text
+-----------------------------------------------------------+
| CCS Simulation Dashboard                                  |
| Configure, run, and visualize simplified CO₂ storage      |
+--------------------------+--------------------------------+
| Input Panel              | Run Summary                    |
| - Porosity               | - Run ID                       |
| - Permeability           | - Status                       |
| - Injection Rate         | - Max Pressure                 |
| - Duration               | - Max Plume Radius             |
| - Grid Size              | - Stored CO₂ Mass              |
| - Random Seed            | - Warnings                     |
| [Run Simulation]         |                                |
+--------------------------+--------------------------------+
| Tabs:                                                     |
| 1. Time Series                                             |
| 2. Spatial Heatmap                                         |
| 3. Scenario Data                                           |
+-----------------------------------------------------------+
```

---

# 5. Input Parameters

The left panel should contain input fields for simplified CCS simulation parameters.

Use Dash components:

```text
dcc.Input
dcc.Slider
dcc.Dropdown
html.Button
dcc.Store
```

Parameters:

```text
porosity: float, range 0.05 to 0.40, default 0.22
permeability: float, range 10 to 1000, default 150
injection_rate: float, range 0.1 to 5.0, default 1.5
duration_days: int, range 30 to 2000, default 365
grid_size: dropdown, options 30x30 / 50x50 / 75x75, default 50x50
well_location: dropdown, options center / left / right, default center
output_variable: dropdown, options pressure / CO2 saturation, default pressure
random_seed: int, default 42
```

Add helpful labels and units, for example:

```text
Porosity [-]
Permeability [mD]
Injection Rate [Mt/year]
Duration [days]
```

---

# 6. Mock Simulator Behavior

Implement a simplified mock simulation in `src/simulator.py`.

Function signature:

```python
def run_mock_ccs_simulation(config: dict) -> dict:
    ...
```

Input:

```python
{
    "porosity": 0.22,
    "permeability": 150,
    "injection_rate": 1.5,
    "duration_days": 365,
    "grid_size": 50,
    "well_location": "center",
    "random_seed": 42
}
```

Output should include:

```python
{
    "time": [...],
    "pressure": [...],
    "co2_saturation": [...],
    "plume_radius": [...],
    "stored_co2_mass": [...],
    "pressure_grids": [...],
    "saturation_grids": [...],
    "summary": {...},
    "warnings": [...]
}
```

The simulator can be mathematically simple and fake but should behave plausibly.

Suggested simplified logic:

### Time axis

Generate 50–100 time steps:

```python
time = np.linspace(0, duration_days, num=80)
```

### Pressure curve

Pressure should increase with injection rate and decrease with permeability:

```text
pressure_baseline = 12 MPa
pressure_buildup ∝ injection_rate / sqrt(permeability)
pressure gradually increases over time
```

Example:

```python
pressure = initial_pressure + pressure_scale * (1 - np.exp(-time / tau))
```

### CO₂ saturation

Saturation increases over time and approaches a cap:

```python
saturation = max_saturation * (1 - np.exp(-time / tau_sat))
```

### Plume radius

Plume radius increases over time:

```python
plume_radius ∝ sqrt(injection_rate * time / porosity)
```

### Stored CO₂ mass

Stored mass should increase approximately linearly:

```python
stored_mass = injection_rate * time / 365
```

### 2D grids

Generate a 2D field for pressure and saturation for selected time steps.

Use a Gaussian plume centered at well location:

```python
field = amplitude * exp(-distance^2 / spread^2)
```

Spread should increase over time.

For pressure grid:

```text
higher near injection well
larger spread over time
higher amplitude with injection rate
lower amplitude with permeability
```

For saturation grid:

```text
higher near well
expands over time
bounded between 0 and 1
```

Add slight heterogeneity/noise based on random seed.

---

# 7. Input Validation

Create `src/validation.py`.

Function:

```python
def validate_config(config: dict) -> list[str]:
    ...
```

Return list of error messages or warnings.

Validation examples:

```text
porosity must be between 0 and 1
permeability must be positive
injection_rate must be positive
duration_days must be positive
```

Warnings:

```text
High injection rate may cause large pressure buildup.
Low permeability may limit CO₂ migration.
Long duration may produce a large plume radius.
```

In the UI:

* Show errors in red.
* Show warnings in yellow/orange.
* Do not run simulation if errors exist.
* Allow run if only warnings exist.

---

# 8. Plotly Visualizations

Create `src/figures.py`.

Implement at least three figure functions.

## 8.1 Time-series figure

Function:

```python
def build_time_series_figure(result: dict) -> go.Figure:
    ...
```

Plot:

```text
pressure vs time
CO₂ saturation vs time
plume radius vs time
```

Either use multiple traces on one chart or separate charts. For the demo, one combined chart with selectable variables is acceptable.

Better: Use tabs or subplots? Since Dash demo should stay simple, use one line chart with multiple traces and clear labels.

Suggested traces:

```text
Max Pressure [MPa]
Average CO₂ Saturation [-]
Plume Radius [m]
```

## 8.2 Spatial heatmap

Function:

```python
def build_heatmap_figure(result: dict, variable: str, time_index: int) -> go.Figure:
    ...
```

Inputs:

```text
variable = "pressure" or "saturation"
time_index = selected by slider
```

Plot:

```text
2D heatmap of pressure or saturation field
```

Add title:

```text
Pressure Field at Day 180
CO₂ Saturation Field at Day 180
```

Use Plotly `go.Heatmap` or `px.imshow`.

## 8.3 Summary / comparison table

Create a Dash DataTable or simple HTML table showing:

```text
Run ID
Duration
Max Pressure
Final Average Saturation
Max Plume Radius
Stored CO₂ Mass
Warnings
```

Optional: Store multiple runs in `dcc.Store` and show a table comparing previous runs.

---

# 9. Interactivity Requirements

Implement these Dash callbacks:

## Callback 1: Run simulation

Trigger:

```text
Run Simulation button
```

State inputs:

```text
porosity
permeability
injection_rate
duration_days
grid_size
well_location
random_seed
```

Behavior:

1. Build config dict.
2. Validate config.
3. If errors, show error message and do not run.
4. Run mock simulator.
5. Generate run_id.
6. Save result into `dcc.Store`.
7. Update summary panel.
8. Update time-series chart.
9. Enable heatmap/time slider.

## Callback 2: Update heatmap

Trigger:

```text
time slider
output variable dropdown
```

State:

```text
current simulation result from dcc.Store
```

Behavior:

1. Select pressure or saturation grid.
2. Select nearest time index.
3. Render heatmap.

## Callback 3: Export results

Optional but useful.

Add buttons:

```text
Download CSV
Download JSON
```

Use Dash `dcc.Download`.

Export:

```text
time-series data as CSV
config + summary as JSON
```

---

# 10. Simulated Status Handling

Since this is pure Dash and mock simulation is fast, add basic fake status to demonstrate workflow.

When clicking Run:

* Show “Running simulation…”
* After result completes, show “Completed”

Optional:

Use a short `time.sleep(0.5)` inside simulation to make it feel like a backend task. Do not make it too slow.

Better UI copy:

```text
Status: Ready
Status: Running
Status: Completed
Status: Validation failed
```

---

# 11. Styling

Use a clean professional style.

Preferred:

```text
white background
cards
clear labels
left input sidebar
charts on the right/bottom
```

Use either:

```text
dash-bootstrap-components
```

or custom CSS in `assets/style.css`.

Avoid over-styling. The goal is interview clarity.

Suggested CSS classes:

```css
.card {
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  background: white;
}

.page {
  padding: 24px;
  font-family: Arial, sans-serif;
}
```

---

# 12. README Requirements

Write a README that explains:

## Project purpose

```text
This is a lightweight Dash + Plotly demo showing how a Python-based CCS simulator can be wrapped into an interactive web dashboard.
```

## Features

```text
- simulation parameter configuration
- mock Python simulator
- input validation
- interactive Plotly time-series
- 2D pressure/saturation heatmap
- time slider
- summary metrics
- optional CSV/JSON export
```

## Local setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Visit:

```text
http://localhost:8050
```

## Docker setup

```bash
docker build -t ccs-dash-demo .
docker run -p 8050:8050 ccs-dash-demo
```

Visit:

```text
http://localhost:8050
```

## Architecture

Include this diagram:

```text
Dash UI
  ↓
Dash callbacks
  ↓
Mock Python simulator
  ↓
pandas / NumPy post-processing
  ↓
Plotly visualizations
```

## Interview note

Mention:

```text
This demo focuses on the software workflow rather than scientific accuracy.
```

---

# 13. Deployment Requirements

Create `Dockerfile`.

Suggested content:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

CMD ["python", "app.py"]
```

In `app.py`, run:

```python
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=False)
```

Optional production command:

```bash
gunicorn app:server --bind 0.0.0.0:8050 --workers 2
```

If using Gunicorn, add it to `requirements.txt`.

---

# 14. Requirements.txt

Suggested:

```text
dash
plotly
pandas
numpy
dash-bootstrap-components
gunicorn
```

Optional:

```text
pytest
```

---

# 15. Minimum Viable Demo Acceptance Criteria

The demo is complete when:

1. `python app.py` starts a Dash server.
2. Browser opens dashboard at `http://localhost:8050`.
3. User can configure CCS parameters.
4. User can click “Run Simulation”.
5. Dashboard displays:

   * status
   * summary metrics
   * interactive time-series chart
   * heatmap
6. Time slider updates heatmap.
7. Output variable dropdown switches between pressure and saturation.
8. Invalid input produces user-friendly validation errors.
9. README explains local and Docker usage.
10. Code is modular and readable.

---

# 16. Stretch Goals

Only implement these after MVP works.

## Stretch Goal 1: Multiple run comparison

Store multiple run results in `dcc.Store`.

Show comparison table:

```text
Run ID
Injection Rate
Porosity
Permeability
Max Pressure
Final Stored CO₂
Max Plume Radius
```

Allow selecting two runs and comparing their pressure curves.

## Stretch Goal 2: Scenario difference heatmap

Show:

```text
Run B pressure field - Run A pressure field
```

## Stretch Goal 3: Background job simulation

Simulate long-running jobs using:

```text
dcc.Interval
job status
run_id
```

Do not overcomplicate with Celery or Redis for this demo.

## Stretch Goal 4: 3D Plotly view

Add optional 3D surface plot:

```text
x, y, pressure field
```

Use Plotly `go.Surface`.

This should be an optional tab, not the main focus.

---

# 17. Important Implementation Guidance

Keep the demo interview-friendly.

Do:

```text
- clear architecture
- clean UI
- readable code
- meaningful variable names
- simple mock physics
- professional README
```

Avoid:

```text
- complex CCS physics
- over-engineered queues
- too many dependencies
- hardcoded global state everywhere
- unreadable callback chains
- 3D animation as the main focus
```

The best story for the demo is:

> This prototype shows how I would wrap a Python-based simulator into an internal scientific dashboard: validated inputs, structured simulation config, Python computation, post-processing, interactive Plotly visualizations, and deployable Dash app.

---

# 18. Suggested Interview Explanation

After the demo is built, I should be able to explain it like this:

> I built this Dash + Plotly prototype to mirror the workflow of a CCS simulator UI. The left panel collects simulation parameters such as porosity, permeability, injection rate, and duration. The Dash callback validates these inputs and passes a structured config into a mock Python simulator. The simulator generates time-series and spatial grid outputs, which are post-processed with NumPy and pandas and visualized using Plotly.
>
> The dashboard includes time-series plots, a 2D heatmap with a time slider, summary metrics, and optional export. The architecture separates UI, validation, simulation logic, post-processing, and visualization modules, so it could be extended to call a real Python simulator later. It can run locally or be deployed on an internal server through Docker or Gunicorn.

---

# 19. Development Order

Ask the coding agent to implement in this order:

```text
1. Create project skeleton
2. Implement mock simulator
3. Implement validation
4. Implement Plotly figure builders
5. Build Dash layout
6. Add run simulation callback
7. Add heatmap callback
8. Add summary panel
9. Add export functionality
10. Add README and Dockerfile
11. Polish styling
12. Test local run
```

---

# 20. Final Deliverable

The final deliverable should be a runnable repository named:

```text
ccs-dash-demo
```

With:

```text
working Dash app
modular source code
requirements.txt
Dockerfile
README
clean professional UI
```

The application should be easy to start with:

```bash
pip install -r requirements.txt
python app.py
```

or:

```bash
docker build -t ccs-dash-demo .
docker run -p 8050:8050 ccs-dash-demo
```
