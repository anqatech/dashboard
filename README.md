# Stock Market Dashboard

Python-first stock market dashboard built around local market datasets and a Dash frontend.

## Current Status

- `dash_app/` is the frontend
- `dashboard_core/` holds shared non-UI logic

## Project Structure

```text
dashboard/
├── dash_app/          # primary Dash frontend
├── dashboard_core/    # shared loaders, analytics, formatters, paths
└── requirements.txt
```

## Setup

1. Create a project-specific Conda environment:

```bash
conda create -n stock-dashboard python=3.12
conda activate stock-dashboard
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. If you are experimenting with Massive.com API calls in notebooks or supporting scripts, keep your API key in `.env`:

```bash
MASSIVE_API_KEY=your_api_key_here
```

## Run The Primary App

Run the Dash app:

```bash
python -m dash_app
```

Open:

```text
http://127.0.0.1:8050
```

## Notes

- The app frontend is Dash.
- Most data, formatting, and analytics logic is shared through `dashboard_core`.
