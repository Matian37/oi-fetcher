from datetime import datetime, timedelta
import os
from pathlib import Path
import re

from playwright.sync_api import Page

from filtering import Task

_COOLDOWN = timedelta(seconds=0.5)
_last_read_time = datetime.now()

def retrieve_subm_code(subm_id: int, page: Page):
    global _last_read_time
    while datetime.now() - _last_read_time < _COOLDOWN:
        pass
    _last_read_time = datetime.now()

    page.goto(f"https://szkopul.edu.pl/s/{subm_id}/source/")

    page.locator("button[id='cpy_btn']").click()
    clipboard_text = page.evaluate("() => navigator.clipboard.readText()")

    assert isinstance(clipboard_text, str)
    return clipboard_text


def gen_file_path(dir_path: Path, task: Task) -> Path:
    score_str = "" if task.score == 100 else str(task.score)
    filename = f"{task.shortname}{score_str}.cpp"
    return Path(dir_path, task.shortname, filename)


def sync_repo(page: Page, tasks: list[Task]):
    solves_path = input("Please enter repo folder:\n")

    if not os.path.isdir(solves_path):
        raise Exception("Path should lead to folder not file")

    if not os.path.exists(solves_path):
        raise Exception("Path not found...")

    repo_path = Path(solves_path, "rozwiazania")
    repo_path.mkdir(exist_ok=True)

    for task in tasks:
        task_dir_path = Path(repo_path, *task.loc)

        best_score = -1

        for entry in task_dir_path.rglob(f"{task.shortname}*.cpp"):
            if not entry.is_file:
                continue

            filename_regex = (
                rf"^{re.escape(task.shortname)}(?:([0-9]{{1,2}}|100))?\.cpp$"
            )
            score = re.match(filename_regex, entry.name)

            if score is None:
                continue

            score = score.groups()[0]
            score = int(score) if score is not None else 100

            best_score = max(best_score, score)

        if best_score >= task.score:
            continue

        print(f"📸 Updating task {task.shortname.upper()} in {task_dir_path} to {task.score}")
        print()

        file_path = gen_file_path(task_dir_path, task)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            f.write(retrieve_subm_code(task.subm_id, page))
