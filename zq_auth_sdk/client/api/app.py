import uuid

from zq_auth_sdk.client.api.base import BaseZqAuthAPI
from zq_auth_sdk.entities.response import ZqAuthResponseType
from zq_auth_sdk.exceptions import (
    ThirdLoginFailedException,
    UserNotFoundException,
    ZqAuthClientException,
)


class ZqAuthApp(BaseZqAuthAPI):
    def test(self):
        """
        测试接口

        https://console-docs.apipost.cn/preview/7abdc86c0ce49501/bf92b4d8832fa312?target_id=ca539c47-8e3e-4314-a560-2913a36294b0  # noqa
        """
        return self._get("/")

    def app_info(self):
        """
        获取 app 信息

        https://console-docs.apipost.cn/preview/7abdc86c0ce49501/bf92b4d8832fa312?target_id=b66a33e6-ae37-4841-a540-69c1c07c133d  # noqa
        """
        return self._get(f"/apps/{self.id}/")

    def sso(self, code: str):
        """
        sso 单点登录 获取用户 union id

        https://console-docs.apipost.cn/preview/7abdc86c0ce49501/bf92b4d8832fa312?target_id=b66a33e6-ae37-4841-a540-69c1c07c133d  # noqa

        :param code: 临时 code

        :raise ThirdLoginFailedException: code 无效
        """
        try:
            return self._post(url="/sso/union-id/", data={"code": code})
        except ZqAuthClientException as e:
            if e.errcode == ZqAuthResponseType.ResourceNotFound.code:
                raise ThirdLoginFailedException(
                    e.errcode, e.errmsg, e.client, e.request, e.response
                )
            else:
                raise e

    def user_info(self, union_id: uuid.UUID | str, detail: bool = True):
        """
        获取用户信息

        https://console-docs.apipost.cn/preview/7abdc86c0ce49501/bf92b4d8832fa312?target_id=1fad0fc0-12f9-4dc2-8ed6-cdffa2b2fd4e  # noqa

        :param union_id: 用户 union id
        :param detail: 是否返回详细信息

        :raise UserNotFountException: union-id 无效 (用户解除绑定)
        """
        if isinstance(union_id, uuid.UUID):
            union_id = union_id.hex

        try:
            return self._get(f"/users/{union_id}/", params={"detail": detail})
        except ZqAuthClientException as e:
            if e.errcode == ZqAuthResponseType.ResourceNotFound.code:
                raise UserNotFoundException(
                    e.errcode, e.errmsg, e.client, e.request, e.response
                )
            else:
                raise e
