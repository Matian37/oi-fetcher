import pytest
import roman

from oi_fetcher.parse import (
    CHECKLIST_DAYS,
    CHECKLIST_MAX_EDITION,
    CHECKLIST_STAGES,
    Location,
    _parse_day,
    _parse_edition,
    _parse_shortname,
    _parse_stage,
    parse_location,
)


class TestParseEdition:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "value",
        ["", "abc", "5 ", "-1", "0", str(CHECKLIST_MAX_EDITION + 1)],
    )
    def test_parse_edition_invalid(self, value: str) -> None:
        with pytest.raises(AssertionError):
            _parse_edition(value)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("value", "expected"),
        [("1", "i"), ("28", "xxviii"), (str(CHECKLIST_MAX_EDITION), "xxxii")],
    )
    def test_parse_edition_valid(self, value: str, expected: str) -> None:
        assert _parse_edition(value) == expected


class TestParseStage:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "value",
        [
            "",
            "etap1",  # the checklist uses the stage codes, not the displayed names
            "e0",
            "e4",
            "E1",
        ],
    )
    def test_parse_stage_invalid(self, value: str) -> None:
        with pytest.raises(AssertionError):
            _parse_stage(value)

    @pytest.mark.unit
    @pytest.mark.parametrize(("value", "expected"), CHECKLIST_STAGES.items())
    def test_parse_stage_valid(self, value: str, expected: str) -> None:
        assert _parse_stage(value) == expected


class TestParseDay:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "value",
        [
            "",
            "dzien0",  # the legacy day-0 alias was replaced by the "d0" code
            "probne",  # the checklist uses the day codes, not the displayed names
            "d4",
            "D1",
        ],
    )
    def test_parse_day_invalid(self, value: str) -> None:
        with pytest.raises(AssertionError):
            _parse_day(value)

    @pytest.mark.unit
    @pytest.mark.parametrize(("value", "expected"), CHECKLIST_DAYS.items())
    def test_parse_day_valid(self, value: str, expected: str) -> None:
        assert _parse_day(value) == expected


class TestParseShortname:
    @pytest.mark.unit
    def test_parse_shortname_invalid(self) -> None:
        with pytest.raises(AssertionError):
            _parse_shortname("")

    @pytest.mark.unit
    def test_parse_shortname_valid(self) -> None:
        assert _parse_shortname("foo") == "foo"


class TestParseLocation:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "location",
        [
            [],
            ["28"],
            ["28", "e1", "d0", "additional"],
            ["invalid", "e1"],
            ["28", "invalid"],
            ["28", "e1", "invalid"],
        ],
    )
    def test_parse_location_invalid(self, location: list[str]) -> None:
        assert parse_location(location) is None

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("edition", "expected"),
        [
            ("0", None),
            ("1", Location("i", "etap1", None)),
            (str(CHECKLIST_MAX_EDITION), Location("xxxii", "etap1", None)),
            (str(CHECKLIST_MAX_EDITION + 1), None),
        ],
    )
    def test_parse_location_edition(
        self, edition: str, expected: Location | None
    ) -> None:
        assert parse_location([edition, "e1"]) == expected

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("location", "expected"),
        [
            (["28", "e2", "d0"], Location("xxviii", "etap2", "probne")),
            (["1", "e2", "d3"], Location("i", "etap2", "dzien3")),
            (
                [str(CHECKLIST_MAX_EDITION), "e3", "d2"],
                Location(
                    roman.toRoman(CHECKLIST_MAX_EDITION).lower(), "etap3", "dzien2"
                ),
            ),
        ],
    )
    def test_parse_location_valid(
        self, location: list[str], expected: Location
    ) -> None:
        assert parse_location(location) == expected

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("stage", "expected"),
        [
            # only the first stage may omit the day
            ("e1", Location("xxviii", "etap1", None)),
            ("e2", None),
            ("e3", None),
        ],
    )
    def test_parse_location_no_day(stage: str, expected: Location | None) -> None:
        assert parse_location(["28", stage]) == expected
