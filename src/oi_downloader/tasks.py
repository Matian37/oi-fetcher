import re
from dataclasses import dataclass
from typing import Final

from oi_downloader.parse import (
    Location,
    parse_location,
    parse_score,
    parse_shortname,
    parse_submission_id,
)
from oi_downloader.web import Website

# Each pattern matches one line of the task archive page and captures one field in
# its named group. They are combined below into a single pass, so fields are visited
# in page order: location, shortname, score. Location has two id formats (location1/2).
LOCATION_PATTERN: Final[str] = (
    r'^\s*+<div\s++class="[^"]++"\s++id="problems-problemgroups-(?P<location1>[^"]++)">[^\S\n]*+$'
    r"|"
    r'^\s*+<div\s++class="[^"]++"\s++id="problemgroups-(?P<location2>\d++-e1)">[^\S\n]*+$'
)
SHORTNAME_PATTERN: Final[str] = (
    r'^\s*+<a\s++href="[^"]++">[\w\s]++\((?P<shortname>[^\)]++)\)\s*+</a>[^\S\n]*+$'
)
SCORE_PATTERN: Final[str] = (
    r'^\s*+<a\s++class="[^"]++"\s++href="(?:https://szkopul\.edu\.pl)?/s/(?P<submission_id>\d++)/">\s*+(?P<score>\d++)\s*+</a>[^\S\n]*+$'
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


def scrape_tasks(website: Website) -> list[Task]:
    """
    Scrapes the tasks from Szkopuł website and returns a list of Task objects.

    Raises: AssertionError if the HTML structure is not as expected.
    """
    html = website.read_tasks_page()

    tasks: list[Task] = []

    last_location: Location | None = None
    last_shortname: str | None = None

    for match in COMBINED_PATTERN.finditer(html):
        unsafe_location = match.group("location1") or match.group("location2")
        unsafe_shortname = match.group("shortname")
        unsafe_submission_id = match.group("submission_id")

        if unsafe_location:
            try:
                last_location = parse_location(unsafe_location.split("-"))
            except AssertionError:
                # skips unsupported locations
                # e.g. stages newer than supported by the checklist
                last_location = None
        elif unsafe_shortname:
            last_shortname = parse_shortname(unsafe_shortname)
        elif unsafe_submission_id:
            submission_id = parse_submission_id(unsafe_submission_id)
            score = parse_score(match.group("score"))

            if last_location is None or last_shortname is None:
                continue

            tasks.append(
                Task(
                    submission_id=submission_id,
                    shortname=last_shortname,
                    score=score,
                    location=last_location,
                )
            )

            # there cannot be task with the same shortname in the same location,
            # so we can reset it to prevent accidental reuse in case of malformed HTML
            last_shortname = None
        else:
            raise NotImplementedError

    return tasks
