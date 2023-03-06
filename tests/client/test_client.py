from datetime import datetime

import pytest

from zq_auth_sdk.client import ZqAuthClient
from zq_auth_sdk.exceptions import AppLoginFailedException


def test_client__login_success(post_mock):
    post_mock("/auth/apps/")

    client = ZqAuthClient(appid="123", secret="123")

    assert client.access_token == "access_token"
    assert client.refresh_token == "refresh_token"
    assert client.id == 9
    assert client.username == "zq_test"
    assert client.name == "测试项目"
    assert client.expire_time == datetime.fromisoformat(
        "2123-03-07T09:16:15.844900Z"
    )


def test_client__refresh_success(post_mock):
    post_mock("/auth/apps/", "expired")
    post_mock("/auth/refresh/", data={"refresh": "refresh_token"})

    client = ZqAuthClient(appid="123", secret="123")  # login here, but expired

    assert client.access_token == "access_token_new"  # refresh here
    assert client.expire_time == datetime.fromisoformat(
        "2123-03-07T10:37:39.081249Z"
    )


def test_client__login_failed(post_mock):
    post_mock("/auth/apps/", "failed")

    with pytest.raises(AppLoginFailedException):
        ZqAuthClient(appid="123", secret="123")
