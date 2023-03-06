import inspect
import logging
from datetime import datetime, timedelta
from typing import Callable

import requests

from zq_auth_sdk.client.api.base import BaseZqAuthAPI
from zq_auth_sdk.entities.response import ZqAuthResponse, ZqAuthResponseType
from zq_auth_sdk.entities.types import JSONVal
from zq_auth_sdk.exceptions import (
    APILimitedException,
    AppLoginFailedException,
    ZqAuthClientException,
)
from zq_auth_sdk.storage import SessionStorage
from zq_auth_sdk.storage.memorystorage import MemoryStorage
from zq_auth_sdk.utils import now

logger = logging.getLogger(__name__)


def _is_api_endpoint(obj):
    return isinstance(obj, BaseZqAuthAPI)


class BaseWeChatClient:
    API_BASE_URL: str = ""

    ACCESS_LIFETIME: timedelta | None = None  # access token的有效期
    REFRESH_LIFETIME: timedelta | None = None  # refresh token的有效期

    _http: requests.Session
    appid: str
    storage: SessionStorage
    timeout: int | None
    auto_retry: bool

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        api_endpoints = inspect.getmembers(self, _is_api_endpoint)
        for name, api in api_endpoints:
            api_cls = type(api)
            api = api_cls(self)
            setattr(self, name, api)
        return self

    def __init__(
        self,
        appid: str,
        access_token: str | None = None,
        storage: SessionStorage | None = None,
        timeout: int | None = None,
        auto_retry: bool = True,
    ):
        self._http = requests.Session()
        self.appid = appid
        self.storage = storage or MemoryStorage()
        self.timeout = timeout
        self.auto_retry = auto_retry

        if access_token:
            self.storage.set(self.access_token_key, access_token)

        if self.API_BASE_URL == "":
            raise Exception("API_BASE_URL is not defined")
        elif self.API_BASE_URL.endswith("/"):
            self.API_BASE_URL = self.API_BASE_URL[:-1]

    # region storage

    # region access
    @property
    def access_token_key(self) -> str:
        """
        access token 缓存key
        """
        return f"{self.appid}_access_token"

    @property
    def access_token(self):
        """ZqAuth access token"""
        access_token = self.storage.get(self.access_token_key)
        if access_token:
            if not self.expire_time:
                # user provided access_token, just return it
                return access_token

            if self.expire_time - now() > timedelta(seconds=60):
                return access_token

        self.refresh_access_token()
        return self.storage.get(self.access_token_key)

    @access_token.setter
    def access_token(self, value):
        self.storage.set(self.access_token_key, value, self.ACCESS_LIFETIME)

    # endregion
    # region expire_time
    @property
    def access_token_expire_time_key(self) -> str:
        """
        access token 过期时间缓存key
        """
        return f"{self.appid}_access_token_expire_time"

    @property
    def expire_time(self) -> datetime | None:
        """
        access token 过期时间
        """
        iso_time = self.storage.get(self.access_token_expire_time_key, None)
        return (
            datetime.fromisoformat(iso_time) if iso_time is not None else None
        )

    @expire_time.setter
    def expire_time(self, value: datetime):
        self.storage.set(self.access_token_expire_time_key, value.isoformat())

    # endregion
    # region refresh
    @property
    def refresh_token_key(self) -> str:
        """
        refresh token 缓存key
        """
        return f"{self.appid}_refresh_token"

    @property
    def refresh_token(self) -> str | None:
        """ZqAuth refresh token"""
        return self.storage.get(self.refresh_token_key, None)

    @refresh_token.setter
    def refresh_token(self, value: str | None):
        if value is None:
            self.storage.delete(self.refresh_token_key)
        self.storage.set(self.refresh_token_key, value, self.REFRESH_LIFETIME)

    # endregion
    # region id
    @property
    def id_key(self) -> str:
        """
        id 缓存key
        """
        return f"{self.appid}_id"

    @property
    def id(self) -> int:
        """ZqAuth id"""
        res = self.storage.get(self.id_key, None)
        if res is None:
            self._login()
        return self.storage.get(self.id_key)

    @id.setter
    def id(self, value: int):
        self.storage.set(self.id_key, value)

    # endregion
    # region name
    @property
    def name_key(self) -> str:
        """
        name 缓存key
        """
        return f"{self.appid}_name"

    @property
    def name(self) -> str:
        """ZqAuth name"""
        res = self.storage.get(self.name_key, None)
        if res is None:
            self._login()
        return self.storage.get(self.name_key)

    @name.setter
    def name(self, value: str):
        self.storage.set(self.name_key, value)

    # endregion
    # region username
    @property
    def username_key(self) -> str:
        """
        username 缓存key
        """
        return f"{self.appid}_username"

    @property
    def username(self) -> str:
        """ZqAuth username"""
        res = self.storage.get(self.username_key, None)
        if res is None:
            self._login()
        return self.storage.get(self.username_key)

    @username.setter
    def username(self, value: str):
        self.storage.set(self.username_key, value)

    # endregion
    # endregion

    def _request(
        self,
        method: str,
        url_or_endpoint: str,
        auth: bool = True,
        params: dict | None = None,
        data: str | bytes | dict | None = None,
        timeout: int | None = None,
        result_processor: Callable[[JSONVal], JSONVal] = None,
        auto_retry: bool | None = None,
        **kwargs,
    ) -> JSONVal:
        """
        发起请求
        :param method: 请求方法
        :param url_or_endpoint: 请求地址
        :param auth: 是否使用token认证（默认开启）
        :param params: 请求query参数
        :param data: 请求体
        :param timeout: 超时时长
        :param result_processor: 结果处理函数
        :param auto_retry: token过期是否自动重试
        :param kwargs:
        :return: JSON 返回
        """
        if not url_or_endpoint.startswith(
            ("http://", "https://")
        ):  # 传入 endpoint
            api_base_url = kwargs.pop("api_base_url", self.API_BASE_URL)
            if api_base_url.endswith("/"):
                api_base_url = api_base_url[:-1]
            url = f"{api_base_url}{url_or_endpoint}"  # base url 拼接到 endpoint 前
        else:
            url = url_or_endpoint

        if not params:
            params = {}
        kwargs["params"] = params
        kwargs["data"] = data
        kwargs["timeout"] = timeout or self.timeout

        if auth:
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Authorization"] = f"Bearer {self.access_token}"

        response = self._http.request(method=method, url=url, **kwargs)  # 发起请求

        logger.debug(f"Request: {method} {url}")

        return self._handle_result(
            response, method, url, result_processor, auto_retry, **kwargs
        )

    def _handle_result(
        self,
        response: requests.Response,
        method: str | None = None,
        url: str | None = None,
        result_processor: Callable[[JSONVal], JSONVal] = None,
        auto_retry: bool | None = None,
        **kwargs,
    ) -> JSONVal:
        response = ZqAuthResponse(response, self)

        if auto_retry is None:
            auto_retry = self.auto_retry

        if response.code != ZqAuthResponseType.Success.code:
            if auto_retry and response.code in [
                ZqAuthResponseType.TokenInvalid.code,
            ]:
                logger.info(
                    "Access token expired, fetch a new one and retry request"
                )
                # 刷新 access token
                self.refresh_access_token()
                # 重试请求
                return self._request(
                    method=method,
                    url_or_endpoint=url,
                    result_processor=result_processor,
                    auto_retry=False,
                    **kwargs,
                )

            elif response.code == ZqAuthResponseType.APIThrottled.code:
                # api freq out of limit
                response.check_exception(APILimitedException)
            else:
                response.check_exception()

        return (
            response.data
            if not result_processor
            else result_processor(response.data)
        )

    def get(
        self,
        url: str,
        auth: bool = True,
        params: dict | None = None,
        data: str | bytes | dict | None = None,
        timeout: int | None = None,
        result_processor: Callable[[JSONVal], JSONVal] = None,
        auto_retry: bool | None = None,
        **kwargs,
    ):
        """
        GET 请求
        :param url: 请求地址
        :param auth: 是否使用token认证（默认开启）
        :param params: 请求query参数
        :param data: 请求体
        :param timeout: 超时时长
        :param result_processor: 结果处理函数
        :param auto_retry: token过期是否自动重试
        :param kwargs:
        :return: JSON 返回
        """
        return self._request(
            method="get",
            url_or_endpoint=url,
            auth=auth,
            params=params,
            data=data,
            timeout=timeout,
            result_processor=result_processor,
            auto_retry=auto_retry,
            **kwargs,
        )

    def post(
        self,
        url: str,
        auth: bool = True,
        params: dict | None = None,
        data: str | bytes | dict | None = None,
        timeout: int | None = None,
        result_processor: Callable[[JSONVal], JSONVal] = None,
        auto_retry: bool | None = None,
        **kwargs,
    ):
        """
        POST 请求
        :param url: 请求地址
        :param auth: 是否使用token认证（默认开启）
        :param params: 请求query参数
        :param data: 请求体
        :param timeout: 超时时长
        :param result_processor: 结果处理函数
        :param auto_retry: token过期是否自动重试
        :param kwargs:
        :return: JSON 返回
        """
        return self._request(
            method="post",
            url_or_endpoint=url,
            auth=auth,
            params=params,
            data=data,
            timeout=timeout,
            result_processor=result_processor,
            auto_retry=auto_retry,
            **kwargs,
        )

    def refresh_access_token(self):
        """fetch access token"""
        logger.info("Fetching access token")
        self._refresh()

    def login(self) -> JSONVal:
        """
        登录接口，用于获取 access_token 和 refresh_token (可选)
        :return: 响应
        """
        raise NotImplementedError()

    def _login(self):
        """
        登录，完善APP信息
        :return:
        """
        logger.info("login using credentials")
        try:
            result = self.login()
        except ZqAuthClientException as e:
            if e.errcode == ZqAuthResponseType.LoginFailed.code:
                logger.error("App login failed, please check your credentials")
                raise AppLoginFailedException(
                    e.errcode, e.errmsg, e.client, e.request, e.response
                )
            else:
                raise e

        self.id = result.get("id")
        self.name = result.get("name")
        self.username = result.get("username")
        self.access_token = result.get("access")
        self.refresh_token = result.get("refresh", None)
        self.expire_time = datetime.fromisoformat(result.get("expire_time"))

    def refresh(self) -> JSONVal:
        """
        刷新 access_token
        """
        raise NotImplementedError()

    def _refresh(self):
        logger.info("refresh access_token")
        if self.refresh_token is None:
            self._login()
            return

        try:
            result = self.refresh()
            self.access_token = result.get("access")
            self.expire_time = datetime.fromisoformat(result.get("expire_time"))
        except ZqAuthClientException as e:
            if (
                e.errcode == ZqAuthResponseType.RefreshTokenInvalid.code
            ):  # refresh token 过期
                self.refresh_token = None
                self._login()
            else:
                raise e
