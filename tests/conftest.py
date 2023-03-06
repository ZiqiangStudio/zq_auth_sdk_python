import json
from pathlib import Path

import pytest
from requests_mock import Mocker

from zq_auth_sdk import ZqAuthClient
from zq_auth_sdk.storage import SessionStorage

_TESTS_PATH = Path(__file__).parent
_FIXTURE_PATH = _TESTS_PATH / "fixtures"


def match_data(request, context):
    if request.body and context:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}
            for item in request.body.split("&"):
                key, sep, value = item.partition("=")
                if sep != "=":
                    raise ValueError("malformed query")
                key = key.split("%")[0]
                if key in data:
                    if isinstance(data[key], list):
                        data[key].append(value)
                    else:
                        data[key] = [data[key], value]
                else:
                    data[key] = value

        for key, value in data.items():
            if key in context:
                if context[key] != value:
                    return False
    return True


def match_params(request, context):
    if request.query and context:
        for key, value in request.query.items():
            if key in context:
                if context[key] != value:
                    return False
    return True


def match_params_and_data(request, params, data):
    return match_params(request, params) and match_data(request, data)


@pytest.fixture
def api_mock(requests_mock: Mocker):
    def _api_mock(
        method: str,
        url: str,
        file_suffix: str | None = None,
        params: dict | None = None,
        data: dict | None = None,
        *kwargs,
    ):
        path = url.replace("/", "_")
        if path.startswith("_"):
            path = path[1:]
        if path.endswith("_"):
            path = path[:-1]

        if file_suffix is not None and file_suffix != "":
            file_suffix = "_" + file_suffix
        else:
            file_suffix = ""

        file = _FIXTURE_PATH / f"{path}{file_suffix}.json"

        with open(file, "r", encoding="utf-8") as f:
            response = json.load(f, strict=False)
        requests_mock.register_uri(
            method,
            f"https://api.cas.ziqiang.net.cn{url}",
            json=response,
            additional_matcher=lambda request: match_params_and_data(
                request, params, data
            ),
            *kwargs,
        )

    return _api_mock


@pytest.fixture
def get_mock(api_mock):
    def _get_mock(
        url: str,
        file_suffix: str | None = None,
        params: dict | None = None,
        *kwargs,
    ):
        api_mock("GET", url, file_suffix, params=params, *kwargs)

    return _get_mock


@pytest.fixture
def post_mock(api_mock):
    def _post_mock(
        url: str,
        file_suffix: str | None = None,
        params: dict | None = None,
        data: dict | None = None,
        *kwargs,
    ):
        api_mock("POST", url, file_suffix, params=params, data=data, *kwargs)

    return _post_mock


@pytest.fixture
def get_client(post_mock):
    def _get_client(
        appid: str = "123",
        secret: str = "123",
        storage: SessionStorage | None = None,
    ):
        post_mock("/auth/apps/")
        return ZqAuthClient(appid=appid, secret=secret, storage=storage)

    return _get_client


@pytest.fixture
def zq_client(get_client):
    return get_client()
