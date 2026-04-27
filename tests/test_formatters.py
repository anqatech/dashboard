from dashboard_core.formatters import (
    format_log_return_as_percent,
    format_market_cap_billions,
    format_percent,
    format_score,
)


def test_format_market_cap_billions() -> None:
    assert format_market_cap_billions(1_500_000_000) == "$1.50b"


def test_format_percent() -> None:
    assert format_percent(0.1234) == "12.3%"


def test_format_log_return_as_percent() -> None:
    assert format_log_return_as_percent(0.0) == "0.0%"


def test_format_score() -> None:
    assert format_score(1.2345) == "1.23"
