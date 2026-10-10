from pathlib import Path

from pytest_mock import MockerFixture

from oi_fetcher import main
from oi_fetcher.exceptions import LoginFailedError


def test_run_login_prompt_success(mocker: MockerFixture) -> None:
    website = mocker.Mock()
    mocker.patch("builtins.input", lambda _: "user")
    mocker.patch.object(main.getpass, "getpass", lambda _: "pass")
    printed = []
    mocker.patch("builtins.print", printed.append)

    main.run_login_prompt(website)

    website.login.assert_called_once_with("user", "pass")
    assert printed == []


def test_run_login_prompt_failure(mocker: MockerFixture) -> None:
    website = mocker.Mock()
    website.login.side_effect = [LoginFailedError(), None]
    mocker.patch("builtins.input", lambda _: "user")
    mocker.patch.object(main.getpass, "getpass", lambda _: "pass")
    printed = []
    mocker.patch("builtins.print", printed.append)

    main.run_login_prompt(website)

    assert printed
    assert website.login.call_count == 2


def _run_repo_path_prompt(
    mocker: MockerFixture,
    tmp_path: Path,
    bad_path: Path | None = None,
) -> None:
    """Runs run_repo_path_prompt with a bad path (if given) and finishes with a valid one.

    Checks if printed error message on a bad path and did not on a good path.
    """
    good = tmp_path / "good"
    good.mkdir()

    paths = [str(bad_path)] if bad_path is not None else []
    paths.append(str(good))

    paths_iter = iter(paths)
    mocker.patch("builtins.input", lambda _: next(paths_iter))
    printed = []
    mocker.patch("builtins.print", printed.append)

    result = main.run_repo_path_prompt()
    assert result == good

    if bad_path is not None:
        assert printed
    else:
        assert printed == []


def test_run_repo_path_prompt_success(mocker: MockerFixture, tmp_path: Path) -> None:
    _run_repo_path_prompt(mocker, tmp_path)


def test_run_repo_path_prompt_invalid(mocker: MockerFixture, tmp_path: Path) -> None:
    _run_repo_path_prompt(mocker, tmp_path, bad_path=Path("\x00"))


def test_run_repo_path_prompt_missing(mocker: MockerFixture, tmp_path: Path) -> None:
    _run_repo_path_prompt(mocker, tmp_path, bad_path=tmp_path / "missing")


def test_run_repo_path_prompt_file(mocker: MockerFixture, tmp_path: Path) -> None:
    file = tmp_path / "file"
    file.write_text("content")
    _run_repo_path_prompt(mocker, tmp_path, bad_path=file)


# TODO: add tests for main function
