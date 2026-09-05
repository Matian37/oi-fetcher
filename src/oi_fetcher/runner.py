import os
import subprocess
import sys
from typing import Final, Self

from playwright.sync_api import (
    Browser,
    Error,
    Page,
    Playwright,
    sync_playwright,
)

from oi_fetcher.exceptions import (
    AlreadyLoggedInError,
    FailedToLaunchBrowserError,
    NotLoggedInError,
    WebsiteNotCompatibleError,
)

LOGIN_PAGE: Final[str] = "https://szkopul.edu.pl/login/"
SUBMISSION_PAGE: Final[str] = "https://szkopul.edu.pl/s/{}/source/"
TASKS_PAGE: Final[str] = "https://szkopul.edu.pl/task_archive/oi/"
BROWSER: Final[str] = "chromium"


def __install_browser() -> None:
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )


def __launch_browser(playwright: Playwright) -> Browser:
    if not os.path.exists(playwright.chromium.executable_path):
        __install_browser()
    return playwright.chromium.launch(headless=True)


class WebsiteRunner:
    __playwright: Playwright
    __browser: Browser
    __page: Page

    logged_in: bool = False

    def __enter__(self) -> Self:
        self.__playwright = sync_playwright().start()

        try:
            self.__browser = __launch_browser(self.__playwright)
        except Exception as e:
            self.__playwright.stop()
            raise FailedToLaunchBrowserError() from e

        self.__page = self.__browser.new_page()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.__page.close()
        self.__browser.close()
        self.__playwright.stop()

    def login(self, login: str, password: str) -> bool:
        if self.logged_in:
            raise AlreadyLoggedInError()

        try:
            if self.__page.url != LOGIN_PAGE:
                self.__page.goto(LOGIN_PAGE)

            self.__page.locator("input[id='id_auth-username']").fill(login)

            passwd_box = self.__page.locator("input[id='id_auth-password']")
            passwd_box.fill(password)

            passwd_box.press("Enter")
        except Error as e:
            raise WebsiteNotCompatibleError from e

        return self.__page.url != LOGIN_PAGE

    def read_submission(self, submission_id: int) -> str:
        if not self.logged_in:
            raise NotLoggedInError()

        try:
            self.__page.goto(SUBMISSION_PAGE.format(submission_id))

            self.__page.locator("button[id='cpy_btn']").click()
            code = self.__page.evaluate("() => navigator.clipboard.readText()")
            assert isinstance(code, str)
        except Error as e:
            raise WebsiteNotCompatibleError from e

        return code

    def read_tasks_page(self) -> str:
        self.__page.goto(TASKS_PAGE)
        return self.__page.content()
