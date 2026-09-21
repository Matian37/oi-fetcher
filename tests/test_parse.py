import pytest

from oi_fetcher.parse import (
    CHECKLIST_DAYS,
    CHECKLIST_STAGES,
    MAX_CHECKLIST_EDITION,
    Location,
    __parse_day,
    __parse_edition,
    __parse_shortname,
    __parse_stage,
    parse_location,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "value",
    ["", "abc", "5 ", "-1", "0", str(MAX_CHECKLIST_EDITION + 1)],
)
def test_parse_edition_invalid(value: str) -> None:
    with pytest.raises(AssertionError):
        __parse_edition(value)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "expected"),
    [("1", "i"), ("28", "xxviii"), (str(MAX_CHECKLIST_EDITION), "xxxii")],
)
def test_parse_edition_valid(value: str, expected: str) -> None:
    assert __parse_edition(value) == expected


@pytest.mark.unit
def test_parse_stage_invalid() -> None:
    with pytest.raises(AssertionError):
        __parse_stage("")


@pytest.mark.unit
@pytest.mark.parametrize("value", CHECKLIST_STAGES)
def test_parse_stage_valid(value: str) -> None:
    assert __parse_stage(value) == value


@pytest.mark.unit
def test_parse_day_invalid() -> None:
    with pytest.raises(AssertionError):
        __parse_day("")


@pytest.mark.unit
def test_parse_day_dzien0() -> None:
    result = __parse_day("dzien0")
    assert result == "probne"
    assert result in CHECKLIST_DAYS


@pytest.mark.unit
@pytest.mark.parametrize("value", CHECKLIST_DAYS)
def test_parse_day_valid(value: str) -> None:
    assert __parse_day(value) == value


@pytest.mark.unit
def test_parse_shortname_invalid() -> None:
    with pytest.raises(AssertionError):
        __parse_shortname("")


@pytest.mark.unit
def test_parse_shortname_valid() -> None:
    assert __parse_shortname("foo") == "foo"


@pytest.mark.unit
@pytest.mark.parametrize(
    "location",
    [
        ["28", "etap1", "probne"],
        [str(MAX_CHECKLIST_EDITION + 1), "etap1", "probne", "x"],
    ],
)
def test_parse_location_invalid(location: list[str]) -> None:
    assert parse_location(location) is None


@pytest.mark.unit
def test_parse_location_valid() -> None:
    result = parse_location(["28", "etap1", "probne", "x"])
    assert result == Location(
        edition="xxviii",
        stage="etap1",
        day="probne",
        shortname="x",
    )
