from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dashboard_core.formatters import format_market_cap_billions, format_percent


class FormatterTests(unittest.TestCase):
    def test_format_market_cap_billions(self) -> None:
        self.assertEqual(format_market_cap_billions(1_500_000_000), "$1.50b")

    def test_format_percent(self) -> None:
        self.assertEqual(format_percent(0.1234), "12.3%")


if __name__ == "__main__":
    unittest.main()
