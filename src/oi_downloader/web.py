import re
from dataclasses import dataclass, field
from html import unescape
from typing import Final

import requests

from oi_downloader.exceptions import (
    AlreadyLoggedInError,
    LoginFailedError,
    MissingCsrfMiddlewareTokenError,
    MissingCsrfTokenError,
    MissingSourceError,
    NotLoggedInError,
    WebsiteError,
)

BASE_URL: Final[str] = "https://szkopul.edu.pl"
HOME_PAGE: Final[str] = f"{BASE_URL}/"
LOGIN_PAGE: Final[str] = f"{BASE_URL}/login/"
TASKS_PAGE: Final[str] = f"{BASE_URL}/task_archive/oi/"
SUBMISSION_PAGE: Final[str] = f"{BASE_URL}/s/{{}}/source/"

CSRF_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'<input\s++type="hidden"\s++name="csrfmiddlewaretoken"\s++value="(?P<csrfmiddlewaretoken>[^"]*)"'
)
SOURCE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'<pre\s++(?:hidden(?:="")?\s++)?id="raw_source">(?P<source>.*?)</pre>',
    flags=re.DOTALL,
)


@dataclass
class Website:
    """
    Client for the Szkopuł website based on plain HTTP requests.

    Can raise WebsiteError.
    """

    csrf_token: str | None = field(default=None, repr=False)
    session_id: str | None = field(default=None, repr=False)
    logged_in: bool = False

    @property
    def _cookies(self) -> dict[str, str]:
        cookies: dict[str, str] = {}

        if self.session_id is not None:
            cookies["sessionid"] = self.session_id
        if self.csrf_token is not None:
            cookies["csrftoken"] = self.csrf_token

        return cookies

    def _read_page(self, url: str) -> str:
        try:
            response = requests.get(url, cookies=self._cookies)
            response.raise_for_status()
        except requests.RequestException as e:
            raise WebsiteError() from e

        csrf_token = response.cookies.get("csrftoken")
        if csrf_token:
            self.csrf_token = csrf_token

        return response.text

    def login(self, login: str, password: str) -> None:
        if self.logged_in:
            raise AlreadyLoggedInError()

        home = self._read_page(HOME_PAGE)

        match = CSRF_PATTERN.search(home)
        if match is None:
            raise MissingCsrfMiddlewareTokenError()

        csrf_middleware_token = match.group("csrfmiddlewaretoken")
        if not csrf_middleware_token:
            raise MissingCsrfMiddlewareTokenError()

        try:
            response = requests.post(
                LOGIN_PAGE,
                data={
                    "csrfmiddlewaretoken": csrf_middleware_token,
                    "login_view-current_step": "auth",
                    "auth-username": login,
                    "auth-password": password,
                },
                cookies=self._cookies,
                headers={"Referer": HOME_PAGE},
                allow_redirects=False,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise WebsiteError() from e

        # Szkopuł returns 200 on failed login and 302 on successful login
        if response.status_code != 302:
            raise LoginFailedError()

        session_id = response.cookies.get("sessionid")
        if session_id is None:
            raise LoginFailedError()

        new_csrf_token = response.cookies.get("csrftoken")
        if new_csrf_token is None:
            raise MissingCsrfTokenError()

        self.session_id = session_id
        self.csrf_token = new_csrf_token
        self.logged_in = True

    def read_tasks_page(self) -> str:
        if not self.logged_in:
            raise NotLoggedInError()
        return self._read_page(TASKS_PAGE)

    def read_submission_code(self, submission_id: int) -> str:
        if not self.logged_in:
            raise NotLoggedInError()

        page = self._read_page(SUBMISSION_PAGE.format(submission_id))

        match = SOURCE_PATTERN.search(page)
        if match is None:
            raise MissingSourceError()

        return unescape(match.group("source"))
