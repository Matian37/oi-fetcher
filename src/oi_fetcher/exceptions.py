class _WebsiteRunnerError(Exception):
    msg: str = "an unexpected website runner error occurred"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.msg)


class AlreadyLoggedInError(_WebsiteRunnerError):
    msg: str = "already logged in"


class NotLoggedInError(_WebsiteRunnerError):
    msg: str = "not logged in"


class WebsiteNotCompatibleError(_WebsiteRunnerError):
    msg: str = (
        "website is not compatible with current version of the tool."
        "Contact the developer with error details for fixes."
    )


class FailedToLaunchBrowserError(_WebsiteRunnerError):
    msg: str = "failed to launch browser"
