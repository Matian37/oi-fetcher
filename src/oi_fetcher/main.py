import getpass

from oi_fetcher.filtering import retrieve_scored_tasks
from oi_fetcher.runner import WebsiteRunner
from oi_fetcher.update import sync_repo


def run_login_prompt(wr: WebsiteRunner):
    while True:
        login = input("Podaj nazwe uzytkownika na szkopule:\n")
        password = getpass.getpass("Podaj haslo (wpisywanie niewidoczne):\n")

        if wr.login(login, password):
            break
        else:
            print("⛔ Logowanie nie powiodlo sie...")


print("🚀 Uruchamianie fetchera...")

with WebsiteRunner() as wr:
    run_login_prompt(wr)
    tasks = retrieve_scored_tasks(wr)
    sync_repo(wr, tasks)

print("✅ Fetcher zakonczyl pobieranie. Zatrzymywanie fetchera...")
