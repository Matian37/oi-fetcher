import os
import re
from pathlib import Path
from time import sleep

from oi_fetcher.filtering import Task
from oi_fetcher.runner import WebsiteRunner


def gen_file_path(dir_path: Path, task: Task) -> Path:
    score_str = "" if task.score == 100 else str(task.score)
    filename = f"{task.shortname}{score_str}.cpp"
    return Path(dir_path, task.shortname, filename)


def sync_repo(wr: WebsiteRunner, tasks: list[Task]):
    solves_path = input("Podaj folder oi zawierajacy checkliste i rozwiazania:\n")

    if not os.path.isdir(solves_path):
        raise Exception("Sciezka wskazuje na plik")

    if not os.path.exists(solves_path):
        raise Exception("Nie znaleziono takowej sciezki...")

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

        print(
            f"📸 Dodawanie zgloszenia o wyniku {task.score} do zadania {task.shortname.upper()}"
        )
        print()

        file_path = gen_file_path(task_dir_path, task)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            f.write(wr.read_submission(task.subm_id))
            sleep(0.5)
