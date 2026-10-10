import pytest
import requests
from helpers import make_response
from pytest_mock import MockerFixture

from oi_downloader.exceptions import (
    AlreadyLoggedInError,
    LoginFailedError,
    MissingCsrfMiddlewareTokenError,
    MissingCsrfTokenError,
    MissingSourceError,
    NotLoggedInError,
    WebsiteError,
)
from oi_downloader.web import (
    HOME_PAGE,
    LOGIN_PAGE,
    LOGOUT_PAGE,
    SUBMISSION_PAGE,
    TASKS_PAGE,
    Website,
)

CSRF_FORM = '<input type="hidden" name="csrfmiddlewaretoken" value="mid">'


class TestCookies:
    @pytest.mark.parametrize(
        ("session_id", "csrf_token", "expected"),
        [
            (None, None, {}),
            ("sid", "tok", {"sessionid": "sid", "csrftoken": "tok"}),
            ("sid", None, {"sessionid": "sid"}),
            (None, "tok", {"csrftoken": "tok"}),
        ],
    )
    def test_cookies(
        self,
        session_id: str | None,
        csrf_token: str | None,
        expected: dict[str, str],
    ) -> None:
        website = Website(session_id=session_id, csrf_token=csrf_token)
        assert website._cookies == expected


class TestReadPage:
    def test_returns_content_and_updates_csrf(self, mocker: MockerFixture) -> None:
        website = Website()
        website.session_id = "sid"
        website.csrf_token = "old"

        response = mocker.Mock()
        response.text = "content"
        response.cookies = {"csrftoken": "new"}
        get = mocker.patch("oi_downloader.web.requests.get", return_value=response)

        assert website._read_page("https://szkopul.edu.pl/contests") == "content"
        assert website.csrf_token == "new"
        get.assert_called_once_with(
            "https://szkopul.edu.pl/contests",
            cookies={"sessionid": "sid", "csrftoken": "old"},
        )

    def test_keeps_csrf_when_absent(self, mocker: MockerFixture) -> None:
        website = Website()
        website.csrf_token = "old"

        response = mocker.Mock()
        response.text = "content"
        response.cookies = {}
        mocker.patch("oi_downloader.web.requests.get", return_value=response)

        assert website._read_page("/") == "content"
        assert website.csrf_token == "old"

    def test_sets_csrf_when_provided(self, mocker: MockerFixture) -> None:
        website = Website()
        website.csrf_token = "old"

        response = mocker.Mock()
        response.text = "content"
        response.cookies = {"csrftoken": "new"}
        mocker.patch("oi_downloader.web.requests.get", return_value=response)

        assert website._read_page("/") == "content"
        assert website.csrf_token == "new"

    def test_raises_on_request_error(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "oi_downloader.web.requests.get",
            side_effect=requests.RequestException,
        )

        with pytest.raises(WebsiteError):
            Website()._read_page("/")


class TestLogin:
    def test_already_logged_in(self) -> None:
        website = Website()
        website.logged_in = True

        with pytest.raises(AlreadyLoggedInError):
            website.login("user", "pass")

    def test_missing_csrf_middleware_token(self, mocker: MockerFixture) -> None:
        home = mocker.Mock()
        home.text = "<html></html>"
        mocker.patch("oi_downloader.web.requests.get", return_value=home)

        with pytest.raises(MissingCsrfMiddlewareTokenError):
            Website().login("user", "pass")

    def test_succeeds_without_csrf_cookie(self, mocker: MockerFixture) -> None:
        home = mocker.Mock()
        home.text = CSRF_FORM
        home.cookies = {}
        mocker.patch("oi_downloader.web.requests.get", return_value=home)

        response = mocker.Mock()
        response.status_code = 302
        response.cookies = {"sessionid": "sid", "csrftoken": "new"}
        mocker.patch("oi_downloader.web.requests.post", return_value=response)

        website = Website()
        website.login("user", "pass")

        assert website.logged_in
        assert website.session_id == "sid"
        assert website.csrf_token == "new"

    def test_success(self, mocker: MockerFixture) -> None:
        home = mocker.Mock()
        home.text = CSRF_FORM
        home.cookies = {"csrftoken": "home-secret"}
        mocker.patch("oi_downloader.web.requests.get", return_value=home)

        response = mocker.Mock()
        response.status_code = 302
        response.cookies = {"sessionid": "sid", "csrftoken": "new"}
        post = mocker.patch("oi_downloader.web.requests.post", return_value=response)

        website = Website()
        website.login("user", "pass")

        assert website.logged_in
        assert website.session_id == "sid"
        assert website.csrf_token == "new"
        post.assert_called_once_with(
            "https://szkopul.edu.pl/login/",
            data={
                "csrfmiddlewaretoken": "mid",
                "login_view-current_step": "auth",
                "auth-username": "user",
                "auth-password": "pass",
            },
            cookies={"csrftoken": "home-secret"},
            headers={"Referer": "https://szkopul.edu.pl/"},
            allow_redirects=False,
        )

    def test_failure(self, mocker: MockerFixture) -> None:
        home = mocker.Mock()
        home.text = CSRF_FORM
        home.cookies = {"csrftoken": "home-secret"}
        mocker.patch("oi_downloader.web.requests.get", return_value=home)

        response = mocker.Mock()
        response.status_code = 200
        response.cookies = {}
        mocker.patch("oi_downloader.web.requests.post", return_value=response)

        website = Website()

        with pytest.raises(LoginFailedError):
            website.login("user", "pass")

        assert not website.logged_in
        assert website.session_id is None

    def test_missing_csrf_in_response(self, mocker: MockerFixture) -> None:
        home = mocker.Mock()
        home.text = CSRF_FORM
        home.cookies = {"csrftoken": "home-secret"}
        mocker.patch("oi_downloader.web.requests.get", return_value=home)

        response = mocker.Mock()
        response.status_code = 302
        response.cookies = {"sessionid": "sid"}
        mocker.patch("oi_downloader.web.requests.post", return_value=response)

        website = Website()

        with pytest.raises(MissingCsrfTokenError):
            website.login("user", "pass")

        assert not website.logged_in
        assert website.session_id is None


class TestLogout:
    def test_requires_login(self) -> None:
        with pytest.raises(NotLoggedInError):
            Website().logout()

    def test_success(self, mocker: MockerFixture) -> None:
        website = Website(session_id="sid", csrf_token="tok")
        website.logged_in = True

        response = mocker.Mock()
        response.raise_for_status = mocker.Mock()
        post = mocker.patch("oi_downloader.web.requests.post", return_value=response)

        website.logout()

        assert not website.logged_in
        assert website.session_id is None
        assert website.csrf_token is None
        post.assert_called_once_with(
            "https://szkopul.edu.pl/logout/",
            data={"csrfmiddlewaretoken": "tok"},
            cookies={"sessionid": "sid", "csrftoken": "tok"},
            headers={"Referer": "https://szkopul.edu.pl/"},
        )

    def test_raises_on_request_error(self, mocker: MockerFixture) -> None:
        website = Website(session_id="sid", csrf_token="tok")
        website.logged_in = True

        mocker.patch(
            "oi_downloader.web.requests.post",
            side_effect=requests.RequestException,
        )

        with pytest.raises(WebsiteError):
            website.logout()


class TestPagesRequireLogin:
    def test_tasks_requires_login(self) -> None:
        with pytest.raises(NotLoggedInError):
            Website().read_tasks_page()

    def test_submission_code_requires_login(self) -> None:
        with pytest.raises(NotLoggedInError):
            Website().read_submission_code(1)


class TestReadTasksPage:
    def test_fetches_archive(self, mocker: MockerFixture) -> None:
        website = Website()
        website.logged_in = True
        _read_page = mocker.patch.object(website, "_read_page", return_value="html")

        assert website.read_tasks_page() == "html"
        _read_page.assert_called_once_with("https://szkopul.edu.pl/task_archive/oi/")


class TestReadSubmissionCode:
    @pytest.mark.parametrize(
        "pre_tag",
        [
            '<pre id="raw_source">',
            '<pre hidden id="raw_source">',
            '<pre hidden="" id="raw_source">',
        ],
    )
    def test_extracts_source(self, mocker: MockerFixture, pre_tag: str) -> None:
        website = Website()
        website.logged_in = True
        html = f"{pre_tag}#include &lt;bits/stdc++.h&gt;\nusing namespace std;\n</pre>"
        _read_page = mocker.patch.object(website, "_read_page", return_value=html)

        assert (
            website.read_submission_code(42)
            == "#include <bits/stdc++.h>\nusing namespace std;\n"
        )
        _read_page.assert_called_once_with("https://szkopul.edu.pl/s/42/source/")

    @pytest.mark.parametrize(
        "html",
        [
            "<html></html>",
            '<pre id="other">code</pre>',
            '<pre class="highlight">code</pre>',
            '<div id="raw_source">code</div>',
        ],
    )
    def test_missing_source(self, mocker: MockerFixture, html: str) -> None:
        website = Website()
        website.logged_in = True
        mocker.patch.object(website, "_read_page", return_value=html)

        with pytest.raises(MissingSourceError):
            website.read_submission_code(42)


class TestWebsiteWorkflow:
    def test_usual_workflow(self, mocker: MockerFixture) -> None:
        TASKS_HTML = (
            '<div class="card" id="problems-problemgroups-10-e2-d0">\n'
            '<a href="foo">Foo (foo)</a>\n'
            '<a class="score" href="/s/101/">50</a>\n'
        )
        SUBMISSION_HTML = '<pre id="raw_source">int main() { return 0; }</pre>'
        SUBM_ID = 101
        CODE = "int main() { return 0; }"

        get_calls: list[tuple[str, dict[str, str] | None]] = []
        post_calls: list[dict] = []

        def fake_get(
            url: str, cookies: dict[str, str] | None = None, **kwargs
        ) -> requests.Response:
            get_calls.append((url, cookies))
            return {
                HOME_PAGE: make_response(CSRF_FORM, cookies={"csrftoken": "csrf-home"}),
                TASKS_PAGE: make_response(TASKS_HTML),
                SUBMISSION_PAGE.format(101): make_response(SUBMISSION_HTML),
            }[url]

        def fake_post(url: str, **kwargs) -> requests.Response:
            post_calls.append({"url": url, **kwargs})
            return {
                LOGIN_PAGE: make_response(
                    status_code=302,
                    cookies={"sessionid": "sid", "csrftoken": "csrf-auth"},
                ),
                LOGOUT_PAGE: make_response(),
            }[url]

        mocker.patch("oi_downloader.web.requests.get", side_effect=fake_get)
        mocker.patch("oi_downloader.web.requests.post", side_effect=fake_post)

        website = Website()

        website.login("user", "pass")
        assert website.logged_in
        assert website.session_id == "sid"
        assert website.csrf_token == "csrf-auth"

        assert website.read_tasks_page() == TASKS_HTML
        assert website.read_submission_code(SUBM_ID) == CODE

        website.logout()
        assert not website.logged_in
        assert website.session_id is None
        assert website.csrf_token is None

        assert get_calls == [
            (HOME_PAGE, {}),
            (TASKS_PAGE, {"sessionid": "sid", "csrftoken": "csrf-auth"}),
            (
                SUBMISSION_PAGE.format(SUBM_ID),
                {"sessionid": "sid", "csrftoken": "csrf-auth"},
            ),
        ]

        assert post_calls == [
            {
                "url": LOGIN_PAGE,
                "data": {
                    "csrfmiddlewaretoken": "mid",
                    "login_view-current_step": "auth",
                    "auth-username": "user",
                    "auth-password": "pass",
                },
                "cookies": {"csrftoken": "csrf-home"},
                "headers": {"Referer": HOME_PAGE},
                "allow_redirects": False,
            },
            {
                "url": LOGOUT_PAGE,
                "data": {"csrfmiddlewaretoken": "csrf-auth"},
                "cookies": {"sessionid": "sid", "csrftoken": "csrf-auth"},
                "headers": {"Referer": HOME_PAGE},
            },
        ]
