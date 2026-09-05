import re

import pydantic
import roman


class Task(pydantic.BaseModel):
    subm_id: int
    score: int
    loc: list[str]
    shortname: str


def _fix_loc(loc: list[str]) -> list[str]:
    checklist_loc = [roman.toRoman(int(loc[0])).lower(), "etap" + loc[1][1]]

    if len(loc) == 3:
        checklist_loc.append("probne" if loc[2][1] == "0" else "dzien" + loc[2][1])

    return checklist_loc


def retrieve_scored_tasks(html: str) -> list[Task]:
    loc_pattern = r'"(?:problems-)?problemgroups-([^"]+)"'
    short_name_pattern = r"\((.*?)\)"
    solved_pattern = (
        r'<a class="badge badge-[^"]*" href="/s/(\d+)/">\s*(\d{1,2}|100)\s*</a>'
    )

    tasks = []

    for match_badge in re.finditer(solved_pattern, html):
        html_before_badge = html[: match_badge.start()]

        subm_id, score = match_badge.groups()

        # get task location
        matches_loc = list(re.finditer(loc_pattern, html_before_badge))
        assert matches_loc
        loc = matches_loc[-1].groups()[0]

        # get task short name
        matches_sname = list(re.finditer(short_name_pattern, html_before_badge))
        assert matches_sname
        shortname = matches_sname[-1].groups()[0]

        # Note: Limitation due to checklist not having ioi elimination and day 3
        if "ioi" in loc or "d3" in loc:
            continue

        tasks.append(
            Task(
                subm_id=int(subm_id),
                score=int(score),
                loc=_fix_loc(loc.split("-")),
                shortname=shortname,
            )
        )
    return tasks
