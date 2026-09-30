import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from oi_fetcher.parse import Location
from oi_fetcher.tasks import Task, scrape_tasks

TESTDATA_DIR = Path(__file__).parent / "testdata"


def load_expected_tasks(name: str) -> list[Task]:
    raw = json.loads((TESTDATA_DIR / f"{name}.out").read_text(encoding="utf-8"))

    return [
        Task(
            submission_id=item["submission_id"],
            shortname=item["shortname"],
            score=item["score"],
            location=Location(
                edition=item["location"]["edition"],
                stage=item["location"]["stage"],
                day=item["location"].get("day"),
            ),
        )
        for item in raw
    ]


class TestScrapeTasks:
    # TODO: add more testdata
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "filename",
        ["some-tasks-solved", "no-tasks-solved"],
    )
    def test_scrape_tasks(self, mocker: MockerFixture, filename: str) -> None:
        wr = mocker.Mock()
        wr.read_tasks_page.return_value = (TESTDATA_DIR / f"{filename}.html").read_text(
            encoding="utf-8"
        )

        tasks = scrape_tasks(wr)
        tasks = sorted(tasks, key=lambda t: t.submission_id)

        expected_tasks = load_expected_tasks(filename)
        expected_tasks = sorted(expected_tasks, key=lambda t: t.submission_id)

        assert tasks == expected_tasks
