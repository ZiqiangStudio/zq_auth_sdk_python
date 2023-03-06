from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zq_auth_sdk import ZqAuthClient


class BaseZqAuthAPI:
    """ZqAuth API base class"""

    API_BASE_URL: str = "https://api.cas.ziqiang.net.cn"
    _client: "ZqAuthClient"

    def __init__(self, client=None):
        self._client = client
        if self.API_BASE_URL and self.API_BASE_URL.endswith("/"):
            self.API_BASE_URL = self.API_BASE_URL[:-1]

    def _get(self, url: str, **kwargs):
        if getattr(self, "API_BASE_URL", None):
            kwargs["api_base_url"] = self.API_BASE_URL
        return self._client.get(url, **kwargs)

    def _post(self, url: str, **kwargs):
        if getattr(self, "API_BASE_URL", None):
            kwargs["api_base_url"] = self.API_BASE_URL
        return self._client.post(url, **kwargs)

    @property
    def access_token(self) -> str:
        return self._client.access_token

    @property
    def refresh_token(self) -> str:
        return self._client.refresh_token

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
