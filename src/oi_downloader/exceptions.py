class WebsiteError(Exception):
    """Base for website errors. Subclasses set a default ``msg``; callers may pass their own."""

    msg: str = "an unexpected website error occurred"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.msg)


class AlreadyLoggedInError(WebsiteError):
    msg: str = "already logged in"


class NotLoggedInError(WebsiteError):
    msg: str = "not logged in"


class LoginFailedError(WebsiteError):
    msg: str = "login failed"


class MissingCsrfTokenError(WebsiteError):
    msg: str = "failed to obtain a CSRF token from the website"


class MissingCsrfMiddlewareTokenError(WebsiteError):
    msg: str = "failed to obtain a CSRF middleware token from the website"


class MissingSourceError(WebsiteError):
    msg: str = "failed to find the submission source on the website"
