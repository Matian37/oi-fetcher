import pytest
import requests
from pytest_mock import MockerFixture

from oi_fetcher.exceptions import (
    AlreadyLoggedInError,
    LoginFailedError,
    MissingCsrfMiddlewareTokenError,
    MissingCsrfTokenError,
    MissingSourceError,
    NotLoggedInError,
    WebsiteError,
)
from oi_fetcher.web import Website

CSRF_FORM = '<input type="hidden" name="csrfmiddlewaretoken" value="tok">'


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
        get = mocker.patch("oi_fetcher.web.requests.get", return_value=response)

        assert website._read_page("https://szkopul.edu.pl/contests") == "content"
        assert website.csrf_token == "new"
        get.assert_called_once_with(
            "https://szkopul.edu.pl/contests",
            cookies={"sessionid": "sid", "csrftoken": "old"},
        )

    def test_raises_when_csrf_absent(self, mocker: MockerFixture) -> None:
        website = Website()
        website.csrf_token = "old"

        response = mocker.Mock()
        response.text = "content"
        response.cookies = {}
        mocker.patch("oi_fetcher.web.requests.get", return_value=response)

        with pytest.raises(MissingCsrfTokenError):
            website._read_page("/")

        assert website.csrf_token == "old"

    def test_raises_on_request_error(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "oi_fetcher.web.requests.get",
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
        mocker.patch("oi_fetcher.web.requests.get", return_value=home)

        with pytest.raises(MissingCsrfMiddlewareTokenError):
            Website().login("user", "pass")

    def test_missing_csrf_cookie(self, mocker: MockerFixture) -> None:
        home = mocker.Mock()
        home.text = CSRF_FORM
        home.cookies = {}
        mocker.patch("oi_fetcher.web.requests.get", return_value=home)

        with pytest.raises(MissingCsrfTokenError):
            Website().login("user", "pass")

    def test_success(self, mocker: MockerFixture) -> None:
        home = mocker.Mock()
        home.text = CSRF_FORM
        home.cookies = {"csrftoken": "home-secret"}
        mocker.patch("oi_fetcher.web.requests.get", return_value=home)

        response = mocker.Mock()
        response.status_code = 302
        response.cookies = {"sessionid": "sid", "csrftoken": "new"}
        post = mocker.patch("oi_fetcher.web.requests.post", return_value=response)

        website = Website()
        website.login("user", "pass")

        assert website.logged_in
        assert website.session_id == "sid"
        assert website.csrf_token == "new"
        post.assert_called_once_with(
            "https://szkopul.edu.pl/login/",
            data={
                "csrfmiddlewaretoken": "tok",
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
        mocker.patch("oi_fetcher.web.requests.get", return_value=home)

        response = mocker.Mock()
        response.status_code = 200
        response.cookies = {}
        mocker.patch("oi_fetcher.web.requests.post", return_value=response)

        website = Website()

        with pytest.raises(LoginFailedError):
            website.login("user", "pass")

        assert not website.logged_in
        assert website.session_id is None

    def test_missing_csrf_in_response(self, mocker: MockerFixture) -> None:
        home = mocker.Mock()
        home.text = CSRF_FORM
        home.cookies = {"csrftoken": "home-secret"}
        mocker.patch("oi_fetcher.web.requests.get", return_value=home)

        response = mocker.Mock()
        response.status_code = 302
        response.cookies = {"sessionid": "sid"}
        mocker.patch("oi_fetcher.web.requests.post", return_value=response)

        website = Website()

        with pytest.raises(MissingCsrfTokenError):
            website.login("user", "pass")

        assert not website.logged_in
        assert website.session_id is None


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
