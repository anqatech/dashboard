import math

import pandas as pd


def format_market_cap_billions(value: float, decimals: int = 2) -> str:
    if pd.isna(value):
        return ""
    billions = float(value) / 1_000_000_000
    return f"${billions:,.{decimals}f}b"


def format_market_cap_billions_whole(value: float) -> str:
    return format_market_cap_billions(value, decimals=0)


def format_percent(value: float, decimals: int = 1) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value) * 100:,.{decimals}f}%"


def format_log_return_as_percent(value: float, decimals: int = 1) -> str:
    if pd.isna(value):
        return ""
    simple_return = math.exp(float(value)) - 1
    return f"{simple_return * 100:,.{decimals}f}%"


def format_score(value: float, decimals: int = 2) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.{decimals}f}"
