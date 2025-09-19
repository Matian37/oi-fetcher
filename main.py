from playwright.sync_api import Browser, Page, sync_playwright

from filtering import retrieve_scored_tasks
from update import sync_repo


def login(page: Page):
    page.goto("https://szkopul.edu.pl/login/")

    login = input("Podaj nazwe uzytkownika na szkopule:\n")
    password = input("Podaj haslo:\n")

    usrbox = page.locator("input[id='id_auth-username']")
    usrbox.fill(login)

    passbox = page.locator("input[id='id_auth-password']")
    passbox.fill(password)
    passbox.press("Enter")


def run(browser: Browser):
    page = browser.new_page()

    login(page)

    page.goto("https://szkopul.edu.pl/task_archive/oi/")
    tasks = retrieve_scored_tasks(page.content())

    sync_repo(page, tasks)

    print("✅ Fetcher zakonczyl pobieranie. Zatrzymywanie fetchera...")


print("🚀 Uruchamianie fetchera...")

with sync_playwright() as playwright:
    browser = playwright.firefox.launch()
    run(browser)
    browser.close()
