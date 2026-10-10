import pytest
import roman

from oi_downloader.parse import (
    CHECKLIST_DAYS,
    CHECKLIST_MAX_EDITION,
    CHECKLIST_STAGES,
    Location,
    _parse_day,
    _parse_edition,
    _parse_stage,
    parse_location,
    parse_score,
    parse_shortname,
    parse_submission_id,
)


class TestParseEdition:
    @pytest.mark.parametrize(
        "value",
        ["", "abc", "5 ", "-1", "0", str(CHECKLIST_MAX_EDITION + 1)],
    )
    def test_parse_edition_invalid(self, value: str) -> None:
        with pytest.raises(AssertionError):
            _parse_edition(value)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("1", "i"), ("28", "xxviii"), (str(CHECKLIST_MAX_EDITION), "xxxii")],
    )
    def test_parse_edition_valid(self, value: str, expected: str) -> None:
        assert _parse_edition(value) == expected


class TestParseStage:
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

    @pytest.mark.parametrize(("value", "expected"), CHECKLIST_STAGES.items())
    def test_parse_stage_valid(self, value: str, expected: str) -> None:
        assert _parse_stage(value) == expected


class TestParseDay:
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

    @pytest.mark.parametrize(("value", "expected"), CHECKLIST_DAYS.items())
    def test_parse_day_valid(self, value: str, expected: str) -> None:
        assert _parse_day(value) == expected


class TestParseShortname:
    def test_parse_shortname_invalid(self) -> None:
        with pytest.raises(AssertionError):
            parse_shortname("")

    def test_parse_shortname_valid(self) -> None:
        assert parse_shortname("foo") == "foo"


class TestParseScore:
    @pytest.mark.parametrize("value", ["", "abc", "-1", "101", "1.0", " 5"])
    def test_parse_score_invalid(self, value: str) -> None:
        with pytest.raises(AssertionError):
            parse_score(value)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("0", 0), ("42", 42), ("100", 100)],
    )
    def test_parse_score_valid(self, value: str, expected: int) -> None:
        assert parse_score(value) == expected


class TestParseSubmissionID:
    @pytest.mark.parametrize("value", ["", "abc", "-1", "1.5", " 5"])
    def test_parse_submission_id_invalid(self, value: str) -> None:
        with pytest.raises(AssertionError):
            parse_submission_id(value)

    @pytest.mark.parametrize(("value", "expected"), [("0", 0), ("123", 123)])
    def test_parse_submission_id_valid(self, value: str, expected: int) -> None:
        assert parse_submission_id(value) == expected


class TestParseLocation:
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
        with pytest.raises(AssertionError):
            parse_location(location)

    @pytest.mark.parametrize(
        ("edition", "expected"),
        [
            ("1", Location("i", "etap1", None)),
            (str(CHECKLIST_MAX_EDITION), Location("xxxii", "etap1", None)),
        ],
    )
    def test_parse_location_edition_valid(
        self, edition: str, expected: Location
    ) -> None:
        assert parse_location([edition, "e1"]) == expected

    @pytest.mark.parametrize(
        "edition",
        ["0", str(CHECKLIST_MAX_EDITION + 1)],
    )
    def test_parse_location_edition_invalid(self, edition: str) -> None:
        with pytest.raises(AssertionError):
            parse_location([edition, "e1"])

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

    def test_parse_location_no_day(self) -> None:
        # only the first stage may omit the day
        assert parse_location(["28", "e1"]) == Location("xxviii", "etap1", None)

    @pytest.mark.parametrize("stage", ["e2", "e3"])
    def test_parse_location_missing_day(self, stage: str) -> None:
        with pytest.raises(AssertionError):
            parse_location(["28", stage])
