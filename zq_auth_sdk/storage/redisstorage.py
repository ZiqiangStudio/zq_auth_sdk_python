import json

from zq_auth_sdk.storage import SessionStorage


class RedisStorage(SessionStorage):
    def __init__(self, redis, prefix="zq_auth"):
        for method_name in ("get", "set", "delete"):
            if not hasattr(redis, method_name):
                raise TypeError(f"redis client must implement {method_name}()")
        self.redis = redis
        self.prefix = prefix

    def key_name(self, key):
        return f"{self.prefix}:{key}"

    def get(self, key, default=None):
        value = self.redis.get(self.key_name(key))
        if value is None:
            return default
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return json.loads(value)

    def set(self, key, value, ttl=None):
        if value is None:
            self.delete(key)
            return
        self.redis.set(self.key_name(key), json.dumps(value), ex=ttl)

    def delete(self, key):
        self.redis.delete(self.key_name(key))
