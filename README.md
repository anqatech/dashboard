# Stock Market Dashboard

Python-first stock market dashboard built around local market datasets and a Dash frontend.

## Structure

```text
dashboard/
├── src/
│   ├── dash_app/         # Dash frontend
│   └── dashboard_core/   # shared loaders, analytics, formatters, paths
├── tests/                # lightweight test suite
└── pyproject.toml        # package metadata and dependencies
```

## Setup

1. Create a project-specific Conda environment:

```bash
conda create -n stock-dashboard python=3.12
conda activate stock-dashboard
```

2. Install the project and its dependencies in editable mode:

```bash
pip install -e .
```

3. If you are experimenting with Massive.com API calls in notebooks or supporting scripts, keep your API key in `.env`:

```bash
MASSIVE_API_KEY=your_api_key_here
```

## Run

Run the Dash app:

```bash
python -m dash_app
```

Open:

```text
http://127.0.0.1:8050
```

## Tests

Run the lightweight test suite with:

```bash
python -m unittest discover tests
```

## Notes

- The app frontend lives in `src/dash_app`.
- Shared non-UI logic lives in `src/dashboard_core`.
- Dependencies now live in `pyproject.toml`, so the project has a single packaging source of truth.
