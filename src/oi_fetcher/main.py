import getpass
from pathlib import Path

from oi_fetcher.sync import sync_repo
from oi_fetcher.tasks import scrape_tasks
from oi_fetcher.web import WebsiteRunner


def run_login_prompt(wr: WebsiteRunner) -> None:
    while True:
        login = input("Podaj nazwe uzytkownika na szkopule:\n")
        password = getpass.getpass("Podaj haslo (wpisywanie niewidoczne):\n")

        if wr.login(login, password):
            break
        else:
            print("⛔ Logowanie nie powiodlo sie...")


def run_repo_path_prompt() -> Path:
    while True:
        repo_path = Path(
            input("Podaj folder oi zawierajacy checkliste i rozwiazania:\n")
        )

        if repo_path.is_dir():
            break
        else:
            print("⛔ Niepoprawna lub nieistniejaca sciezka do folderu.")

    return repo_path


def main():
    print("🚀 Uruchamianie fetchera...")

    with WebsiteRunner() as wr:
        run_login_prompt(wr)
        tasks = scrape_tasks(wr)
        repo_path = run_repo_path_prompt()
        sync_repo(wr, tasks, repo_path)

    print("✅ Wszystko jest juz aktualne.")


if __name__ == "__main__":
    main()
