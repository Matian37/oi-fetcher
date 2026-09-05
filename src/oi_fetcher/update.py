import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from time import sleep
from typing import Final

from oi_fetcher.runner import WebsiteRunner
from oi_fetcher.tasks import Task

UPDATE_COLLDOWN: Final[float] = 0.5


def gen_submission_regex(task: Task) -> str:
    assert task.shortname.isalnum()
    return rf"^{re.escape(task.shortname)}(?:([0-9]{{1,2}}|100))?\.cpp$"


def gen_subm_directory(repo_path: Path, task: Task) -> Path:
    return Path(
        repo_path,
        task.location.edition,
        task.location.stage,
        task.location.day,
        task.shortname,
    )


# TODO: get info what file format to use for submission
def gen_subm_file_path(repo_path: Path, task: Task) -> Path:
    score_str = "" if task.score == 100 else str(task.score)
    return gen_subm_directory(repo_path, task) / f"{task.shortname}{score_str}.cpp"


def match_task(task: Task, filename: str) -> int | None:
    """
    Returns the score from the filename as an integer if the filename matches the task's submission regex.
    Otherwise, returns None.
    """
    match = re.match(gen_submission_regex(task), filename)
    return int(match.group(1) or 100) if match else None


def cleanup_directory(dir: Path, keep_file: str = "") -> None:
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


def max_local_submission(task: Task, task_dir: Path) -> Submission | None:
    best_score = -1
    best_filename: str | None = None

    for entry in task_dir.glob("*"):
        if entry.is_dir():
            continue

        score = match_task(task, entry.name)
        if score is None:
            continue

        if best_score < score:
            best_score = score
            best_filename = entry.name

    if best_filename is None:
        return None
    return Submission(best_filename, best_score)


def save_solution(task: Task, task_dir: Path, wr: WebsiteRunner) -> Path:
    """
    Fetches the solution for the given task and saves it to the task directory.
    Returns the path to the saved file.
    """
    subm_file_path = gen_subm_file_path(task_dir, task)
    subm_file_path.parent.mkdir(parents=True, exist_ok=True)

    with subm_file_path.open("w", encoding="utf-8") as f:
        f.write(wr.read_submission(task.submission_id))

    return subm_file_path


def sync_repo(wr: WebsiteRunner, tasks: list[Task], repo_path: Path) -> None:
    solutions_dir = Path(repo_path, "rozwiazania")
    solutions_dir.mkdir(exist_ok=True)

    for task in tasks:
        task_dir = gen_subm_directory(repo_path, task)

        max_submission = max_local_submission(task, task_dir)

        if max_submission is None or max_submission.score < task.score:
            print(
                f"📸 Dodawanie zgloszenia  do zadania {task.shortname.upper()} o wyniku {task.score}",
            )
            subm_file_path = save_solution(task, task_dir, wr)
            cleanup_directory(task_dir, keep_file=subm_file_path.name)
            sleep(UPDATE_COLLDOWN)
        else:
            cleanup_directory(task_dir, keep_file=max_submission.filename)
