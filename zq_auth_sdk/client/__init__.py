from zq_auth_sdk.client.api.app import ZqAuthApp
from zq_auth_sdk.client.base import DEFAULT_API_BASE_URL, BaseZqAuthClient
from zq_auth_sdk.entities.types import JSONVal


class ZqAuthClient(BaseZqAuthClient):
    """Client for the ZqAuth HTTP API. Usable from any Python framework."""

    ACCESS_LIFETIME: int | None = 24 * 60 * 60
    REFRESH_LIFETIME: int | None = 10 * 24 * 60 * 60

    app = ZqAuthApp()

    def __init__(
        self,
        appid: str,
        secret: str,
        *,
        api_base_url: str = DEFAULT_API_BASE_URL,
        storage=None,
        timeout: int | None = None,
        auto_retry: bool = True,
    ):
        super().__init__(
            appid, api_base_url, storage, timeout, auto_retry
        )
        self.secret = secret
        self.refresh_access_token()

    def login(self) -> JSONVal:
        return self.post(
            url="/auth/apps/",
            data={"app_key": self.appid, "app_secret": self.secret},
            auth=False,
        )

    def refresh(self) -> JSONVal:
        return self.post(
            url="/auth/refresh/",
            data={"refresh": self.refresh_token},
            auth=False,
        )
