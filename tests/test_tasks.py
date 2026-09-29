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
            location=Location(**item["location"]),
        )
        for item in raw
    ]


class TestScrapeTasks:
    # FIX: some-tasks-solved failing
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "name",
        ["some-tasks-solved", "no-tasks-solved"],
    )
    def test_scrape_tasks(self, mocker: MockerFixture, name: str) -> None:
        wr = mocker.Mock()
        wr.read_tasks_page.return_value = (TESTDATA_DIR / f"{name}.html").read_text(
            encoding="utf-8"
        )

        assert scrape_tasks(wr) == load_expected_tasks(name)
