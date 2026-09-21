import pytest

from oi_fetcher.exceptions import _WebsiteRunnerError


@pytest.mark.unit
def test_default_message() -> None:
    assert str(_WebsiteRunnerError()) == _WebsiteRunnerError.msg


@pytest.mark.unit
def test_custom_message() -> None:
    assert str(_WebsiteRunnerError("custom")) == "custom"
