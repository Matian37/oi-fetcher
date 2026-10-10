import pytest

from oi_fetcher.exceptions import WebsiteError


@pytest.mark.unit
def test_default_message() -> None:
    assert str(WebsiteError()) == WebsiteError.msg


@pytest.mark.unit
def test_custom_message() -> None:
    assert str(WebsiteError("custom")) == "custom"
