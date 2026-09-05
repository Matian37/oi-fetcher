import getpass

from oi_fetcher.runner import WebsiteRunner
from oi_fetcher.tasks import scrape_tasks
from oi_fetcher.update import sync_repo


def run_login_prompt(wr: WebsiteRunner):
    while True:
        login = input("Podaj nazwe uzytkownika na szkopule:\n")
        password = getpass.getpass("Podaj haslo (wpisywanie niewidoczne):\n")

        if wr.login(login, password):
            break
        else:
            print("⛔ Logowanie nie powiodlo sie...")


def main():
    print("🚀 Uruchamianie fetchera...")

    with WebsiteRunner() as wr:
        run_login_prompt(wr)
        tasks = scrape_tasks(wr)
        sync_repo(wr, tasks)

    print("✅ Fetcher zakonczyl pobieranie. Zatrzymywanie fetchera...")


if __name__ == "__main__":
    main()
