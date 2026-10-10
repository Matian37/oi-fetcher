import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from time import sleep
from typing import Final

from oi_downloader.tasks import Task
from oi_downloader.web import Website

UPDATE_COLLDOWN: Final[float] = 0.5
SOLUTIONS_FOLDER: Final[str] = "rozwiazania"


def _gen_submission_regex(task: Task) -> str:
    """
    Returns a regex pattern that matches submission filenames for the given task.
    It only matches filenames according to the checklist rules, which requires them to be in cpp format.
    """
    assert task.shortname.isalnum()
    return rf"^{re.escape(task.shortname)}(?:([0-9]{{1,2}}|100))?\.cpp$"


def _gen_subm_directory(repo_path: Path, task: Task) -> Path:
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
    Returns the path to the submission file for the given task in the repository.
    Due to checklist limitations, the filename must be in cpp format.
    Otherwise, the file will be rejected.
    """
    score_str = "" if task.score == 100 else str(task.score)
    return _gen_subm_directory(repo_path, task) / f"{task.shortname}{score_str}.cpp"


def _match_task(task: Task, filename: str) -> int | None:
    """
    Returns the score from the filename as an integer if the filename matches the task's submission regex.
    Otherwise, returns None.
    """
    match = re.match(_gen_submission_regex(task), filename)
    return int(match.group(1) or 100) if match else None


def _cleanup_directory(dir: Path, keep_file: str = "") -> None:
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
            sleep(UPDATE_COLLDOWN)
        else:
            _cleanup_directory(task_dir, keep_file=max_submission.filename)
