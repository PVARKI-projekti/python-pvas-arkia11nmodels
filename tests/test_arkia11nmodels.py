"""Package level tests"""
from arkia11nmodels import __version__


def test_version() -> None:
    """Make sure version matches expected"""
    assert __version__ == "1.0.1"
