import getpass
from pathlib import Path

from oi_fetcher.exceptions import LoginFailedError
from oi_fetcher.sync import sync_repo
from oi_fetcher.tasks import scrape_tasks
from oi_fetcher.web import Website


def run_login_prompt(website: Website) -> None:
    while True:
        login = input("Enter your Szkopuł username:\n")
        password = getpass.getpass("Enter your password (input hidden):\n")

        try:
            website.login(login, password)
            break
        except LoginFailedError:
            print("⛔ Login failed...")


def run_repo_path_prompt() -> Path:
    while True:
        repo_path = Path(
            input("Enter repo folder containing the checklist and solutions:\n")
        )

        if repo_path.is_dir():
            break
        else:
            print("⛔ Invalid or non-existent folder path.")

    return repo_path


def main():
    print("🚀 Starting the fetcher...")

    website = Website()
    run_login_prompt(website)
    tasks = scrape_tasks(website)
    repo_path = run_repo_path_prompt()
    sync_repo(website, tasks, repo_path)

    print("✅ Everything is up to date.")


if __name__ == "__main__":
    main()
