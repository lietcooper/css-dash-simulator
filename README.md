# CCS Simulation Dashboard

This is a lightweight Dash + Plotly demo showing how a Python-based CCS (Carbon Capture and Storage) simulator can be wrapped into an interactive web dashboard. Users configure simulation parameters, run a mock simulation, inspect summary metrics, and explore time-series and spatial results through interactive Plotly visualizations.

## Features

- Simulation parameter configuration (porosity, permeability, injection rate, duration, grid size, well location, random seed)
- Mock Python simulator producing time-series and 2D grid outputs
- Input validation with errors and warnings
- Interactive Plotly time-series (pressure, CO₂ saturation, plume radius)
- 2D pressure / saturation heatmap with a time slider
- Run summary metrics and status badge
- Scenario history table for comparing multiple runs
- CSV and JSON export of the latest run

## Local Setup

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

## Docker Setup

```bash
docker build -t ccs-dash-demo .
docker run -p 8050:8050 ccs-dash-demo
```

Visit:

```text
http://localhost:8050
```

For a production-style run with Gunicorn:

```bash
gunicorn app:server --bind 0.0.0.0:8050 --workers 2
```

## Architecture

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

## Project Structure

```text
ccs-dash-demo/
├── app.py                  Dash layout and callbacks
├── requirements.txt
├── Dockerfile
├── README.md
├── data/
│   └── sample_runs/        Reserved for cached run artifacts
├── src/
│   ├── __init__.py
│   ├── simulator.py        Mock CCS simulation logic
│   ├── postprocess.py      Raw arrays to pandas DataFrames / summaries
│   ├── figures.py          Plotly figure builders
│   └── validation.py       Input range / type validation
└── assets/
    └── style.css           Custom styling
```