from zq_auth_sdk.client import api
from zq_auth_sdk.client.base import BaseWeChatClient
from zq_auth_sdk.entities.types import JSONVal


class ZqAuthClient(BaseWeChatClient):

    """
    zq auth API 操作类
    通过这个类可以操作Auth API。
    """

    API_BASE_URL = "https://api.cas.ziqiang.net.cn"

    ACCESS_LIFETIME: int | None = 1 * 24 * 60 * 60  # 1天
    REFRESH_LIFETIME: int | None = 10 * 24 * 60 * 60  # 10天

    app = api.ZqAuthApp()

    def __init__(
        self,
        appid,
        secret,
        access_token=None,
        storage=None,
        timeout=None,
        auto_retry=True,
    ):
        """
        zq auth api 访问

        https://console-docs.apipost.cn/preview/7abdc86c0ce49501/bf92b4d8832fa312

        :param appid: APP_KEY_ID
        :param secret: APP_KEY_SECRET
        :param access_token: access token (可选)
        :param storage: 存储后端
        :param timeout: 请求超时时长
        :param auto_retry: token过期后是否刷新后重试(默认开启)

        :raise AppLoginFailedException: appid 与 secret 错误

        """
        super().__init__(appid, access_token, storage, timeout, auto_retry)
        self.appid = appid
        self.secret = secret

        self.refresh_access_token()

    def login(self) -> JSONVal:
        """
        app 登录

        https://console-docs.apipost.cn/preview/7abdc86c0ce49501/bf92b4d8832fa312?target_id=f3dd4470-fee8-4bcf-a9f1-7570c4392068
        """
        return self.post(
            url="/auth/apps/",
            data={
                "app_key": self.appid,
                "app_secret": self.secret,
            },
            auth=False,
        )

    def refresh(self) -> JSONVal:
        """
        刷新 token

        https://console-docs.apipost.cn/preview/7abdc86c0ce49501/bf92b4d8832fa312?target_id=07dafe85-2142-4b00-8477-47d8350a9a54
        """
        return self.post(
            url="/auth/refresh/",
            data={
                "refresh": self.refresh_token,
            },
            auth=False,
        )
