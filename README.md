# Stock Market Dashboard

Minimal first slice for a Python-first stock dashboard using Massive.com data.

## What this does

- accepts one stock ticker
- fetches recent daily aggregate bars from Massive.com
- plots closing prices in a simple Streamlit chart
- shows the underlying rows in a table

## Why this is small on purpose

This repo starts with one app file and a few setup files so the flow stays easy to review:

- Python UI
- one external API call
- simple data shaping
- simple chart

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

3. Add your Massive API key to your existing `.env` file:

```bash
MASSIVE_API_KEY=your_api_key_here
```

## Run

```bash
streamlit run app.py
```

## Next likely steps

- add a company summary/header
- compare multiple tickers
- add intraday charts
- introduce a small service layer once the app grows
