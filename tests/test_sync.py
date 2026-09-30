import re
from dataclasses import dataclass
from pathlib import Path

import pytest
from pytest_mock import MockerFixture, MockType

from oi_fetcher.parse import Location
from oi_fetcher.sync import (
    Submission,
    cleanup_directory,
    gen_subm_directory,
    gen_subm_file_path,
    gen_submission_regex,
    match_task,
    max_local_submission,
    save_solution,
    sync_repo,
)
from oi_fetcher.tasks import Task


def make_task(
    shortname: str = "sho",
    score: int = 100,
    submission_id: int = 1,
    edition: str = "xxviii",
    stage: str = "etap1",
    day: str | None = "probne",
) -> Task:
    return Task(
        submission_id=submission_id,
        shortname=shortname,
        score=score,
        location=Location(
            edition=edition,
            stage=stage,
            day=day,
        ),
    )


class TestGenSubmissionRegex:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "shortname",
        [
            "",
            # shortnames that would need regex escaping are rejected by the assertion
            "x.cpp",
            "a+b",
            r"\d",
            "x y",
            "x*",
        ],
    )
    def test_invalid_shortname(self, shortname: str) -> None:
        with pytest.raises(AssertionError):
            gen_submission_regex(make_task(shortname=shortname))

    @pytest.mark.unit
    def test_valid_shortname(self) -> None:
        pattern = gen_submission_regex(make_task(shortname="abc"))
        assert re.match(pattern, "abc.cpp")

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("filename", "expected_group"),
        [
            ("x.cpp", None),
            ("x0.cpp", "0"),
            ("x99.cpp", "99"),
            ("x100.cpp", "100"),
        ],
    )
    def test_matches(self, filename: str, expected_group: str | None) -> None:
        match = re.match(gen_submission_regex(make_task(shortname="x")), filename)
        assert match is not None
        assert match.group(1) == expected_group

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "filename",
        [
            "x.cpp ",  # trailing space
            "y.cpp",  # different shortname
            "x101.cpp",  # score out of range
            "x-1.cpp",  # negative score
            "x.py",  # wrong extension
            "xcpp",  # missing dot
        ],
    )
    def test_does_not_match(self, filename: str) -> None:
        assert (
            re.match(gen_submission_regex(make_task(shortname="x")), filename) is None
        )


class TestGenSubmDirectory:
    @pytest.mark.unit
    def test_returns_expected_path(self, tmp_path: Path) -> None:
        task = make_task(
            shortname="sho",
            edition="xxviii",
            stage="etap1",
            day="probne",
        )
        assert gen_subm_directory(tmp_path, task) == (
            tmp_path / "xxviii" / "etap1" / "probne" / "sho"
        )

    @pytest.mark.unit
    def test_omits_missing_day(self, tmp_path: Path) -> None:
        task = make_task(
            shortname="sho",
            edition="xxx",
            stage="etap1",
            day=None,
        )
        assert gen_subm_directory(tmp_path, task) == tmp_path / "xxx" / "etap1" / "sho"


class TestGenSubmFilePath:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("score", "expected_name"),
        [(0, "sho0.cpp"), (42, "sho42.cpp"), (100, "sho.cpp")],
    )
    def test_returns_expected_path(
        self, tmp_path: Path, score: int, expected_name: str
    ) -> None:
        task = make_task(shortname="sho", score=score)
        path = gen_subm_file_path(tmp_path, task)
        assert path.name == expected_name
        assert path == gen_subm_directory(tmp_path, task) / expected_name


class TestMatchTask:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("x.cpp", 100),
            ("x100.cpp", 100),
            ("x0.cpp", 0),
            ("x99.cpp", 99),
            ("y.cpp", None),
            ("x101.cpp", None),
            ("x.py", None),
        ],
    )
    def test_returns_score_or_none(self, filename: str, expected: int | None) -> None:
        assert match_task(make_task(shortname="x"), filename) == expected


class TestCleanupDirectory:
    @pytest.mark.unit
    def test_empty_dir(self, tmp_path: Path) -> None:
        cleanup_directory(tmp_path)
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.unit
    def test_removes_files_and_nested_dirs(self, tmp_path: Path) -> None:
        (tmp_path / "a.cpp").write_text("a")
        (tmp_path / "b.txt").write_text("b")

        nested = tmp_path / "nested"
        nested.mkdir()
        (nested / "c.cpp").write_text("c")

        cleanup_directory(tmp_path)

        assert list(tmp_path.iterdir()) == []

    @pytest.mark.unit
    def test_keeps_file(self, tmp_path: Path) -> None:
        keep = tmp_path / "keep.cpp"
        keep.write_text("keep")
        (tmp_path / "remove.cpp").write_text("remove")

        cleanup_directory(tmp_path, keep_file="keep.cpp")

        assert keep.read_text() == "keep"
        assert not (tmp_path / "remove.cpp").exists()

    @pytest.mark.unit
    def test_removes_dir_with_kept_name(self, tmp_path: Path) -> None:
        # a directory sharing the kept file's name must still be removed
        same_name_dir = tmp_path / "keep.cpp"
        same_name_dir.mkdir()
        (same_name_dir / "inner.cpp").write_text("inner")

        cleanup_directory(tmp_path, keep_file="keep.cpp")

        assert not same_name_dir.exists()


class TestMaxLocalSubmission:
    @pytest.mark.unit
    def test_no_tasks(self, tmp_path: Path) -> None:
        assert max_local_submission(make_task(shortname="x"), tmp_path) is None

    @pytest.mark.unit
    def test_different_shortnames(self, tmp_path: Path) -> None:
        # two files with a different shortname from searched one
        (tmp_path / "y1.cpp").write_text("")
        (tmp_path / "y2.cpp").write_text("")

        assert max_local_submission(make_task(shortname="x"), tmp_path) is None

    @pytest.mark.unit
    def test_picks_matching_task(self, tmp_path: Path) -> None:
        (tmp_path / "x50.cpp").write_text("")
        (tmp_path / "y49.cpp").write_text("")

        result = max_local_submission(make_task(shortname="y"), tmp_path)

        assert result == Submission(filename="y49.cpp", score=49)

    @pytest.mark.unit
    def test_returns_best_score(self, mocker: MockerFixture) -> None:
        # mock the directory so that entry iteration order is deterministic
        # scores resolved from the names are 31, 100, no match and 11 respectively
        names = ["x31.cpp", "x100.cpp", "bad.cpp", "x11.cpp"]

        entries = []
        for name in names:
            entry = mocker.Mock()
            entry.is_dir.return_value = False
            entry.name = name
            entries.append(entry)

        task_dir = mocker.Mock()
        task_dir.glob.return_value = entries

        result = max_local_submission(make_task(shortname="x"), task_dir)

        assert result == Submission(filename="x100.cpp", score=100)
        task_dir.glob.assert_called_once_with("*")


class TestSaveSolution:
    @pytest.mark.unit
    def test_creates_parent_folders(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        wr = mocker.Mock()
        wr.read_submission.return_value = "code"
        task = make_task(shortname="sho", score=42, submission_id=7)

        path = save_solution(task, tmp_path, wr)

        assert path == gen_subm_file_path(tmp_path, task)
        assert path.read_text() == "code"
        wr.read_submission.assert_called_once_with(7)

    @pytest.mark.unit
    def test_parent_folders_exist(self, tmp_path: Path, mocker: MockerFixture) -> None:
        wr = mocker.Mock()
        wr.read_submission.return_value = "code"
        task = make_task(shortname="sho", score=42, submission_id=3)
        gen_subm_directory(tmp_path, task).mkdir(parents=True)

        path = save_solution(task, tmp_path, wr)

        assert path == gen_subm_file_path(tmp_path, task)
        assert path.read_text() == "code"
        wr.read_submission.assert_called_once_with(3)

    @pytest.mark.unit
    def test_overwrites_existing_file(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        wr = mocker.Mock()
        wr.read_submission.return_value = "old code"
        task = make_task(shortname="sho", score=42)

        path = save_solution(task, tmp_path, wr)
        assert path.read_text() == "old code"

        wr.read_submission.return_value = "new code"
        result = save_solution(task, tmp_path, wr)

        assert result == path
        assert path.read_text() == "new code"
        assert wr.read_submission.call_count == 2


@dataclass
class SyncRun:
    read_submission: MockType
    sleep: MockType
    printed: list[str]


def _run_sync(
    mocker: MockerFixture,
    repo_path: Path,
    tasks: list[Task],
    code: str | list[str] = "code",
) -> SyncRun:
    wr = mocker.Mock()
    if isinstance(code, list):
        codes = {task.submission_id: c for task, c in zip(tasks, code, strict=True)}
        wr.read_submission.side_effect = lambda submission_id: codes[submission_id]
    else:
        wr.read_submission.return_value = code

    sleep = mocker.patch("oi_fetcher.sync.sleep")
    printed: list[str] = []
    mocker.patch("builtins.print", printed.append)

    sync_repo(wr, tasks, repo_path)

    return SyncRun(
        read_submission=wr.read_submission,
        sleep=sleep,
        printed=printed,
    )


class TestSyncRepo:
    @pytest.mark.unit
    def test_creates_solutions_dir(self, tmp_path: Path, mocker: MockerFixture) -> None:
        run = _run_sync(mocker, tmp_path, [])

        assert (tmp_path / "rozwiazania").is_dir()
        run.read_submission.assert_not_called()
        run.sleep.assert_not_called()
        assert run.printed == []

    @pytest.mark.unit
    @pytest.mark.parametrize("day", [None, "d1"])
    def test_new_submission_to_new_task(
        self, tmp_path: Path, mocker: MockerFixture, day: str | None
    ) -> None:
        (tmp_path / "rozwiazania").mkdir()
        task = make_task(shortname="sho", score=100, submission_id=3, day=day)

        run = _run_sync(mocker, tmp_path, [task])

        assert (gen_subm_directory(tmp_path, task) / "sho.cpp").read_text() == "code"
        run.read_submission.assert_called_once_with(3)
        run.sleep.assert_called_once()
        assert run.printed  # check that the notice was printed

    @pytest.mark.unit
    def test_better_submission_to_old_task(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        (tmp_path / "rozwiazania").mkdir()
        task = make_task(shortname="sho", score=100)
        task_dir = gen_subm_directory(tmp_path, task)
        task_dir.mkdir(parents=True)
        (task_dir / "sho50.cpp").write_text("old")
        (task_dir / "dummy.txt").write_text("dummy")
        (task_dir / "dummy_dir").mkdir()

        run = _run_sync(mocker, tmp_path, [task])

        assert (task_dir / "sho.cpp").read_text() == "code"
        assert not (task_dir / "sho50.cpp").exists()
        assert not (task_dir / "dummy.txt").exists()
        assert not (task_dir / "dummy_dir").exists()
        run.read_submission.assert_called_once()
        run.sleep.assert_called_once()
        assert run.printed  # check that the notice was printed

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "local_name",
        [
            "sho.cpp",  # local score is better than the remote one
            "sho99.cpp",  # local score is equal to the remote one
        ],
    )
    def test_keeps_better_or_equal_submission(
        self,
        tmp_path: Path,
        mocker: MockerFixture,
        local_name: str,
    ) -> None:
        (tmp_path / "rozwiazania").mkdir()
        task = make_task(shortname="sho", score=99)
        task_dir = gen_subm_directory(tmp_path, task)
        task_dir.mkdir(parents=True)
        (task_dir / local_name).write_text("local")
        (task_dir / "dummy.txt").write_text("dummy")

        run = _run_sync(mocker, tmp_path, [task])

        assert (task_dir / local_name).read_text() == "local"
        assert not (task_dir / "dummy.txt").exists()
        run.read_submission.assert_not_called()
        run.sleep.assert_not_called()
        assert run.printed == []

    @pytest.mark.unit
    def test_multiple_tasks(self, tmp_path: Path, mocker: MockerFixture) -> None:
        (tmp_path / "rozwiazania").mkdir()
        first = make_task(shortname="aaa", score=100, submission_id=1)
        second = make_task(shortname="bbb", score=50, submission_id=2)

        run = _run_sync(
            mocker, tmp_path, [first, second], code=["first code", "second code"]
        )

        assert (
            gen_subm_directory(tmp_path, first) / "aaa.cpp"
        ).read_text() == "first code"
        assert (
            gen_subm_directory(tmp_path, second) / "bbb50.cpp"
        ).read_text() == "second code"
        assert run.read_submission.call_count == 2
        assert run.sleep.call_count == 2
        assert len(run.printed) == 2
