from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zq_auth_sdk.client import ZqAuthClient


class BaseZqAuthAPI:
    _client: "ZqAuthClient"

    def __init__(self, client: "ZqAuthClient | None" = None):
        self._client = client

    def _get(self, url: str, **kwargs):
        return self._client.get(url, **kwargs)

    def _post(self, url: str, **kwargs):
        return self._client.post(url, **kwargs)

    @property
    def access_token_expire_time(self) -> datetime:
        return self._client.expire_time

    @property
    def id(self) -> int:
        return self._client.id

    @property
    def app_username(self) -> str:
        return self._client.username

    @property
    def app_name(self) -> str:
        return self._client.name

    @property
    def storage(self):
        return self._client.storage

    @property
    def appid(self) -> str:
        return self._client.appid

    @property
    def secret(self) -> str:
        return self._client.secret
