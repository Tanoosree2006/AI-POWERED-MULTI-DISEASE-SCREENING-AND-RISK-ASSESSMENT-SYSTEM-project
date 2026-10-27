import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    """Train once if no saved model exists, so tests can run on a fresh clone."""
    import config
    if not config.MODEL_PATH.exists():
        import train
        train.main()
    return config.MODEL_PATH
