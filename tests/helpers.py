import requests
from requests.cookies import cookiejar_from_dict


def make_response(
    text: str = "",
    status_code: int = 200,
    cookies: dict[str, str] | None = None,
) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = text.encode("utf-8")
    response.cookies = cookiejar_from_dict(cookies or {})
    return response
