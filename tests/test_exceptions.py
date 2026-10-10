from oi_fetcher.exceptions import WebsiteError


def test_default_message() -> None:
    assert str(WebsiteError()) == WebsiteError.msg


def test_custom_message() -> None:
    assert str(WebsiteError("custom")) == "custom"
