import getpass
import sys
from pathlib import Path

from oi_downloader.exceptions import LoginFailedError
from oi_downloader.sync import sync_repo
from oi_downloader.tasks import scrape_tasks
from oi_downloader.web import Website


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

    try:
        tasks = scrape_tasks(website)
    except AssertionError as e:
        print(f"🚨 Error occurred (contact developer with full error log): {e}")
        sys.exit(1)

    repo_path = run_repo_path_prompt()
    sync_repo(website, tasks, repo_path)

    print("✅ Everything is up to date.")
    sys.exit(0)


if __name__ == "__main__":
    main()
