import getpass
from pathlib import Path

from oi_fetcher.exceptions import LoginFailedError
from oi_fetcher.sync import sync_repo
from oi_fetcher.tasks import scrape_tasks
from oi_fetcher.web import Website


def run_login_prompt(website: Website) -> None:
    while True:
        login = input("Podaj nazwe uzytkownika na szkopule:\n")
        password = getpass.getpass("Podaj haslo (wpisywanie niewidoczne):\n")

        try:
            website.login(login, password)
            break
        except LoginFailedError:
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

    website = Website()
    run_login_prompt(website)
    tasks = scrape_tasks(website)
    repo_path = run_repo_path_prompt()
    sync_repo(website, tasks, repo_path)

    print("✅ Wszystko jest juz aktualne.")


if __name__ == "__main__":
    main()
