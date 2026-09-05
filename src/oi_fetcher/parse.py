from dataclasses import dataclass
from typing import Final

import roman

MAX_CHECKLIST_EDITION: Final[int] = 32
CHECKLIST_STAGES: Final[set[str]] = {"etap1", "etap2", "etap3"}
CHECKLIST_DAYS: Final[set[str]] = {"probne", "dzien1", "dzien2", "dzien3"}


@dataclass
class Location:
    edition: str
    stage: str
    day: str
    shortname: str


def __parse_edition(value: str) -> str:
    assert value.isdecimal()
    edition = int(value)

    assert edition <= MAX_CHECKLIST_EDITION

    return roman.toRoman(edition).lower()


def __parse_stage(value: str) -> str:
    if value == "dzien0":
        value = "probne"
    assert value in CHECKLIST_STAGES
    return value


def __parse_day(value: str) -> str:
    assert value in CHECKLIST_DAYS
    return value


def __parse_shortname(value: str) -> str:
    assert value
    return value


def parse_location(location: list[str]) -> Location | None:
    if len(location) != 4:
        return None

    edition, stage, day, shortname = location

    try:
        return Location(
            edition=__parse_edition(edition),
            stage=__parse_stage(stage),
            day=__parse_day(day),
            shortname=__parse_shortname(shortname),
        )
    except AssertionError:
        return None
