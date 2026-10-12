"""
Synchronises a local OI checklist repository with submissions from Szkopuł.

A submission is stored as::

    <solutions folder>/<edition>/<stage>[/<day>]/<shortname>/<shortname><score>.cpp

The score suffix is omitted for 100 points. Only the best-scoring submission for
a task is kept; any other files in its folder are removed.
"""

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from time import sleep
from typing import Final

from oi_downloader.tasks import Task
from oi_downloader.web import Website

# delay between requests to avoid overloading the website
UPDATE_COOLDOWN: Final[float] = 0.5
SOLUTIONS_FOLDER: Final[str] = "rozwiazania"


def _gen_submission_regex(task: Task) -> str:
    """
    Returns a regex matching the checklist filenames of a task.
    The optional capture group is the score suffix (empty means 100).
    Only ``.cpp`` filenames match, as required by the checklist.
    """
    assert task.shortname.isalnum()
    return rf"^{re.escape(task.shortname)}(?:([0-9]{{1,2}}|100))?\.cpp$"


def _gen_subm_directory(repo_path: Path, task: Task) -> Path:
    """Returns path to the directory where the submission for the given task should be stored in the repository."""
    path: list[str] = [
        str(repo_path),
        SOLUTIONS_FOLDER,
        task.location.edition,
        task.location.stage,
    ]

    if task.location.day is not None:
        path.append(task.location.day)

    path.append(task.shortname)

    return Path(*path)


def _gen_subm_file_path(repo_path: Path, task: Task) -> Path:
    """
    Returns the checklist path of the task's submission file.
    The file must use the ``.cpp`` extension, as required by the checklist.
    """
    score_str = "" if task.score == 100 else str(task.score)
    return _gen_subm_directory(repo_path, task) / f"{task.shortname}{score_str}.cpp"


def _match_task(task: Task, filename: str) -> int | None:
    """
    Returns the score from the filename as an integer,
    or None if the filename does not match the task's submission regex.
    """
    match = re.match(_gen_submission_regex(task), filename)
    return int(match.group(1) or 100) if match else None


def _cleanup_directory(dir: Path, keep_file: str = "") -> None:
    """Removes all files and subdirectories in ``dir``, except a file named ``keep_file``."""
    for entry in dir.glob("*"):
        if entry.is_dir():
            shutil.rmtree(entry)
            continue

        if entry.name == keep_file:
            continue
        entry.unlink()


@dataclass
class Submission:
    filename: str
    score: int


def _max_local_submission(task: Task, task_dir: Path) -> Submission | None:
    """Returns the best-scoring local submission for a task in ``task_dir``, or None if there is none."""
    best_subm: tuple[int, str] = (-1, "")

    for entry in task_dir.glob("*"):
        if entry.is_dir():
            continue

        score = _match_task(task, entry.name)
        if score is None:
            continue

        best_subm = max(best_subm, (score, entry.name))

    # if no submission was found, return None
    if best_subm[0] == -1:
        return None
    return Submission(filename=best_subm[1], score=best_subm[0])


def _save_solution(task: Task, repo_path: Path, website: Website) -> Path:
    """
    Fetches the solution for the given task and saves it to the task directory.
    Returns the path to the saved file.
    """
    subm_file_path = _gen_subm_file_path(repo_path, task)
    subm_file_path.parent.mkdir(parents=True, exist_ok=True)

    with subm_file_path.open("w", encoding="utf-8") as f:
        f.write(website.read_submission_code(task.submission_id))

    return subm_file_path


def sync_repo(website: Website, tasks: list[Task], repo_path: Path) -> None:
    """Downloads any task submission that beats the best one already stored locally."""
    solutions_dir = Path(repo_path, SOLUTIONS_FOLDER)
    solutions_dir.mkdir(exist_ok=True)

    for task in tasks:
        task_dir = _gen_subm_directory(repo_path, task)

        max_submission = _max_local_submission(task, task_dir)

        if max_submission is None or max_submission.score < task.score:
            print(
                f"📸 Dodawanie zgloszenia  do zadania {task.shortname.upper()} o wyniku {task.score}",
            )
            subm_file_path = _save_solution(task, repo_path, website)
            _cleanup_directory(task_dir, keep_file=subm_file_path.name)
            sleep(UPDATE_COOLDOWN)
        else:
            _cleanup_directory(task_dir, keep_file=max_submission.filename)
