import re
from dataclasses import dataclass
from typing import Final

from oi_fetcher.parse import Location, parse_location
from oi_fetcher.web import WebsiteRunner

LOCATION_PATTERN: Final[str] = (
    r'^\s*+<div\s++class="[^"]++"\s++id="problems-problemgroups-(?P<location1>[^"]++)">[^\S\n]*+$'
    r"|"
    r'^\s*+<div\s++class="[^"]++"\s++id="problemgroups-(?P<location2>\d++-e1)">[^\S\n]*+$'
)
SHORTNAME_PATTERN: Final[str] = (
    r'^\s*+<a\s++href="[^"]++">[\w\s]++\((?P<shortname>[^\)]++)\)\s*+</a>[^\S\n]*+$'
)
SCORE_PATTERN: Final[str] = (
    r'^\s*+<a\s++class="[^"]++"\s++href="/s/(?P<submission>\d++)/">\s*+(?P<score>\d++)\s*+</a>[^\S\n]*+$'
)

COMBINED_PATTERN: Final[re.Pattern] = re.compile(
    rf"(?:{LOCATION_PATTERN})|(?:{SHORTNAME_PATTERN})|(?:{SCORE_PATTERN})",
    flags=re.MULTILINE,
)


@dataclass
class Task:
    submission_id: int
    shortname: str
    score: int
    location: Location


def scrape_tasks(wr: WebsiteRunner) -> list[Task]:
    html = wr.read_tasks_page()

    tasks: list[Task] = []

    last_location: Location | None = None
    last_shortname: str | None = None

    for match in COMBINED_PATTERN.finditer(html):
        location_group = match.group("location1") or match.group("location2")

        # TODO: parse shortname and submission params for safety
        if location_group:
            last_location = parse_location(location_group.split("-"))
        elif match.group("shortname"):
            last_shortname = match.group("shortname")
        elif match.group("submission"):
            subm_id = match.group("submission")
            score = match.group("score")

            if last_location is None or last_shortname is None:
                continue

            tasks.append(
                Task(
                    submission_id=int(subm_id),
                    shortname=last_shortname,
                    score=int(score),
                    location=last_location,
                )
            )
        else:
            raise NotImplementedError

    return tasks
