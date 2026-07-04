import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: end-to-end reproduction guards (bootstrap over committed clouds)",
    )
