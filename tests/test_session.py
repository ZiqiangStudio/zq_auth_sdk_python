import os
from datetime import datetime

import pytest

_TESTS_PATH = os.path.abspath(os.path.dirname(__file__))
_FIXTURE_PATH = os.path.join(_TESTS_PATH, "fixtures")


def test_memory_session_storage_init(get_client):
    from zq_auth_sdk.storage.memorystorage import MemoryStorage

    client = get_client()

    assert isinstance(client.storage, MemoryStorage)

    assert client.access_token == "access_token"
    assert client.refresh_token == "refresh_token"
    assert client.id == 9
    assert client.username == "zq_test"
    assert client.name == "测试项目"
    assert client.expire_time == datetime.fromisoformat(
        "2123-03-07T09:16:15.844900Z"
    )


def test_redis_session_storage_init(get_client):
    from fakeredis import FakeStrictRedis

    from zq_auth_sdk.storage.redisstorage import RedisStorage

    redis = FakeStrictRedis()
    storage = RedisStorage(redis)
    client = get_client(storage=storage)
    assert isinstance(client.storage, RedisStorage)

    assert client.access_token == "access_token"
    assert client.refresh_token == "refresh_token"
    assert client.id == 9
    assert client.username == "zq_test"
    assert client.name == "测试项目"
    assert client.expire_time == datetime.fromisoformat(
        "2123-03-07T09:16:15.844900Z"
    )


@pytest.mark.skip(reason="memcached not support")
def test_memcached_storage_init(get_client):
    from pymemcache.client import Client

    from zq_auth_sdk.storage.memcachedstorage import MemcachedStorage

    servers = ("127.0.0.1", 11211)
    memcached = Client(servers)
    storage = MemcachedStorage(memcached)
    client = get_client(storage=storage)
    assert isinstance(client.storage, MemcachedStorage)

    assert client.access_token == "access_token"
    assert client.refresh_token == "refresh_token"
    assert client.id == 9
    assert client.username == "zq_test"
    assert client.name == "测试项目"
    assert client.expire_time == datetime.fromisoformat(
        "2123-03-07T09:16:15.844900Z"
    )
