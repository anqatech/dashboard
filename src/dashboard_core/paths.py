from pathlib import Path


DATA_ROOT = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data")
FRAMES_DIR = DATA_ROOT / "frames"
DAILY_BARS_DIR = DATA_ROOT / "daily-bars"
UNIVERSE_PATH = DATA_ROOT / "sp500" / "tickers_enriched.csv"

STATUS_FRAME_PATH = FRAMES_DIR / "daily-bars-database-status-with-market-cap.parquet"
PERFORMANCE_FRAME_PATH = FRAMES_DIR / "daily-bars-performance-metrics.parquet"
VOLATILITY_FRAME_PATH = FRAMES_DIR / "daily-bars-realized-volatility.parquet"
TREND_FRAME_PATH = FRAMES_DIR / "daily-bars-trend-signals.parquet"
