import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from oi_downloader.parse import Location
from oi_downloader.tasks import Task, scrape_tasks

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

    @pytest.mark.parametrize(
        "parser_name",
        # all parsers except parse_location must not suppress errors
        ["parse_shortname", "parse_submission_id", "parse_score"],
    )
    def test_propagates_parse_assertion(
        self, mocker: MockerFixture, parser_name: str
    ) -> None:
        mocker.patch(f"oi_downloader.tasks.{parser_name}", side_effect=AssertionError)
        html = """
        <div class="x" id="problems-problemgroups-10-e2-d0">
        <a href="x">Foo (foo)</a>
        <a class="x" href="/s/1/">50</a>
        """
        website = mocker.Mock()
        website.read_tasks_page.return_value = html

        with pytest.raises(AssertionError):
            scrape_tasks(website)

    def test_skips_unsupported_location(self, mocker: MockerFixture) -> None:
        # edition 9999 is newer than the checklist supports, so its tasks is skipped
        # but second task is supported and should be returned
        html = """
        <div class="x" id="problems-problemgroups-9999-e2-d0">
        <a href="x">Foo (foo)</a>
        <a class="x" href="/s/1/">100</a>
        <div class="x" id="problems-problemgroups-10-e2-d0">
        <a href="x">Bar (bar)</a>
        <a class="x" href="/s/2/">50</a>
        """
        website = mocker.Mock()
        website.read_tasks_page.return_value = html

        tasks = scrape_tasks(website)
        assert tasks == [
            Task(
                submission_id=2,
                shortname="bar",
                score=50,
                location=Location(edition="x", stage="etap2", day="probne"),
            )
        ]

    def test_resets_shortname_after_task(self, mocker: MockerFixture) -> None:
        # a submission without a preceding shortname must be ignored,
        # so the same shortname is not accidentally reused
        html = """
        <div class="x" id="problems-problemgroups-10-e2-d0">
        <a href="x">Foo (foo)</a>
        <a class="x" href="/s/1/">50</a>
        <a class="x" href="/s/2/">60</a>
        """
        website = mocker.Mock()
        website.read_tasks_page.return_value = html

        tasks = scrape_tasks(website)
        assert tasks == [
            Task(
                submission_id=1,
                shortname="foo",
                score=50,
                location=Location(edition="x", stage="etap2", day="probne"),
            )
        ]
