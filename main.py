import os

from playwright.sync_api import Browser, Page, sync_playwright
from PIL import Image

from filtering import retrieve_scored_tasks
from update import sync_repo


def print_page(page: Page):
    os.remove("test.png")
    page.screenshot(path="test.png")
    img = Image.open("test.png")
    img.show()


def login(page: Page):
    page.goto("https://szkopul.edu.pl/login/")

    login = input("Please enter login:\n")
    password = input("Please enter password:\n")

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

    print("✅ Fetcher job done. Stopping fetcher...")


print("🚀 Starting fetcher...")

with sync_playwright() as playwright:
    browser = playwright.firefox.launch()
    run(browser)
    browser.close()
