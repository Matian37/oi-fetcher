import re
from dataclasses import dataclass

from oi_fetcher.parse import Location, parse_location
from oi_fetcher.runner import WebsiteRunner

LOCATION_PATTERN = r'"(?:problems-)?problemgroups-([^"]+)"'
SUBMISSION_PATTERN = (
    r'<a class="badge badge-[^"]*" href="/s/(\d+)/">\s*(\d{1,2}|100)\s*</a>'
)
COMBINED_PATTERN = re.compile(
    rf"(?P<location>{LOCATION_PATTERN})|(?P<submission>{SUBMISSION_PATTERN})"
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

    location: Location | None = None

    for match in COMBINED_PATTERN.finditer(html):
        if match.group("location"):
            location = parse_location(match.group("location").split("-"))

        if match.group("submission"):
            subm_id, score = match.group("submission")

        if location:
            tasks.append(
                Task(
                    submission_id=int(subm_id),
                    shortname=location.shortname,
                    score=int(score),
                    location=location,
                )
            )

    return tasks
