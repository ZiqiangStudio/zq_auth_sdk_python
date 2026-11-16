"""Exceptions raised by zq_auth_sdk."""


class ZqAuthException(Exception):
    def __init__(self, errcode, errmsg):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"Error code: {errcode}, message: {errmsg}")


class ZqAuthClientException(ZqAuthException):
    def __init__(
        self, errcode, errmsg, client=None, request=None, response=None
    ):
        super().__init__(errcode, errmsg)
        self.client = client
        self.request = request
        self.response = response


class AppLoginFailedException(ZqAuthClientException):
    """The app key or app secret was rejected."""


class ThirdLoginFailedException(ZqAuthClientException):
    """The one-time SSO code was rejected."""


class UserNotFoundException(ZqAuthClientException):
    """The UnionID has no matching user."""


class APILimitedException(ZqAuthClientException):
    """The ZqAuth API rate limit was reached."""
