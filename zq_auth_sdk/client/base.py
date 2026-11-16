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

DEFAULT_API_BASE_URL = "https://api.cas.ziqiang.net.cn"

logger = logging.getLogger(__name__)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _is_api_endpoint(obj):
    return isinstance(obj, BaseZqAuthAPI)


class BaseZqAuthClient:
    ACCESS_LIFETIME: timedelta | None = None
    REFRESH_LIFETIME: timedelta | None = None

    _http: requests.Session
    appid: str
    api_base_url: str
    storage: SessionStorage
    timeout: int | None
    auto_retry: bool

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        api_endpoints = inspect.getmembers(self, _is_api_endpoint)
        for name, api in api_endpoints:
            api_cls = type(api)
            setattr(self, name, api_cls(self))
        return self

    def __init__(
        self,
        appid: str,
        api_base_url: str,
        storage: SessionStorage | None = None,
        timeout: int | None = None,
        auto_retry: bool = True,
    ):
        if not appid or not api_base_url:
            raise ValueError("appid and api_base_url are required")

        self._http = requests.Session()
        self.appid = appid
        self.api_base_url = api_base_url.rstrip("/")
        self.storage = storage or MemoryStorage()
        self.timeout = timeout
        self.auto_retry = auto_retry

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

            if self.expire_time - datetime.now().astimezone() > timedelta(
                seconds=60
            ):
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
        iso_time = self.storage.get(self.access_token_expire_time_key)
        return _parse_datetime(iso_time) if iso_time is not None else None

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
            return
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
        if not url_or_endpoint.startswith(("http://", "https://")):
            url = f"{self.api_base_url}{url_or_endpoint}"
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

        response = self._http.request(
            method=method, url=url, **kwargs
        )  # 发起请求

        logger.debug("Request: %s %s", method, url)

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

        self.id = result["id"]
        self.name = result["name"]
        self.username = result["username"]
        self.access_token = result["access"]
        self.refresh_token = result.get("refresh")
        self.expire_time = _parse_datetime(result["expire_time"])

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
            self.access_token = result["access"]
            self.expire_time = _parse_datetime(result["expire_time"])
        except ZqAuthClientException as e:
            if (
                e.errcode == ZqAuthResponseType.RefreshTokenInvalid.code
            ):  # refresh token 过期
                self.refresh_token = None
                self._login()
            else:
                raise e
