from dataclasses import dataclass
from typing import Final

import roman

CHECKLIST_MAX_EDITION: Final[int] = 32

CHECKLIST_STAGES: Final[dict[str, str]] = {
    "e1": "etap1",
    "e2": "etap2",
    "e3": "etap3",
}

CHECKLIST_DAYS: Final[dict[str, str]] = {
    "d0": "probne",
    "d1": "dzien1",
    "d2": "dzien2",
    "d3": "dzien3",
}


@dataclass
class Location:
    """
    Represents a location in the OI checklist with already parsed values.
    """

    edition: str
    stage: str
    day: str | None


def _parse_edition(value: str) -> str:
    assert value.isdecimal()
    edition = int(value)

    assert 0 < edition <= CHECKLIST_MAX_EDITION

    return roman.toRoman(edition).lower()


def _parse_stage(value: str) -> str:
    assert value in CHECKLIST_STAGES
    return CHECKLIST_STAGES[value]


def _parse_day(value: str) -> str:
    assert value in CHECKLIST_DAYS
    return CHECKLIST_DAYS[value]


def parse_shortname(value: str) -> str:
    assert value
    return value


def parse_location(location: list[str]) -> Location:
    assert len(location) >= 2
    assert len(location) == (2 if location[1] == "e1" else 3)

    return Location(
        edition=_parse_edition(location[0]),
        stage=_parse_stage(location[1]),
        day=_parse_day(location[2]) if len(location) == 3 else None,
    )


def parse_score(value: str) -> int:
    assert value.isdigit()
    score = int(value)
    assert 0 <= score <= 100
    return score


def parse_submission_id(value: str) -> int:
    assert value.isdigit()
    submission_id = int(value)
    return submission_id
