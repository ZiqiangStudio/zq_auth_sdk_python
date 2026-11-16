from datetime import datetime


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
        "2123-03-07T09:16:15.844900+00:00"
    )


def test_redis_session_storage_init(get_client):
    from fakeredis import FakeStrictRedis

    from zq_auth_sdk.storage.redisstorage import RedisStorage

    storage = RedisStorage(FakeStrictRedis())
    client = get_client(storage=storage)

    assert isinstance(client.storage, RedisStorage)
    assert client.access_token == "access_token"
    assert client.refresh_token == "refresh_token"
    assert client.id == 9
    assert client.username == "zq_test"
    assert client.name == "测试项目"
    assert client.expire_time == datetime.fromisoformat(
        "2123-03-07T09:16:15.844900+00:00"
    )
