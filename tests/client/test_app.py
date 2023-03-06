import pytest

from zq_auth_sdk.exceptions import (
    ThirdLoginFailedException,
    UserNotFoundException,
)


def test_test(zq_client, get_mock):
    get_mock("/")

    res = zq_client.app.test()
    assert res == {
        "user": {
            "id": 9,
            "username": "zq_test",
            "type": 2,
            "is_active": True,
            "is_superuser": False,
        },
        "time": "2023-03-06T18:26:53.713365+08:00",
    }


def test_app_info(zq_client, get_mock):
    get_mock("/apps/9/")
    res = zq_client.app.app_info()

    assert res == {
        "id": 9,
        "username": "zq_test",
        "name": "测试项目",
        "is_active": True,
    }


def test_sso(zq_client, post_mock):
    post_mock("/sso/union-id/", data={"code": "12345"})

    res = zq_client.app.sso("12345")

    assert res == {"union_id": "678574dd4a274d3cbfac10666b7613ef"}


def test_sso_failed(zq_client, post_mock):
    post_mock("/sso/union-id/", "failed", data={"code": "12345"})

    with pytest.raises(ThirdLoginFailedException):
        zq_client.app.sso("12345")


def test_user_info(zq_client, get_mock):
    get_mock("/users/123/")

    res = zq_client.app.user_info("123")

    assert res == {
        "name": "测试",
        "student_id": "2020302111311",
        "phone": "18312341233",
        "is_certified": True,
        "certify_time": "2023-03-04T20:42:00+08:00",
        "update_time": "2023-03-06T10:49:07.976501+08:00",
    }


def test_user_info_no_detail(zq_client, get_mock):
    get_mock("/users/123/", "no_detail")

    res = zq_client.app.user_info("123")

    assert res == {"certify_time": "2023-03-04T20:42:00+08:00"}


def test_user_info_not_found(zq_client, get_mock):
    get_mock("/users/123/", "not_found")

    with pytest.raises(UserNotFoundException):
        zq_client.app.user_info("123")
