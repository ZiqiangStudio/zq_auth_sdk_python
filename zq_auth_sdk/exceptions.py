"""
    zq_auth_sdk.exceptions
    ~~~~~~~~~~~~~~~~~~~~

    基本异常定义
"""


class ZqAuthException(Exception):
    """Base exception for zq_auth_sdk"""

    def __init__(self, errcode, errmsg):
        """
        :param errcode: Error code
        :param errmsg: Error message
        """
        self.errcode = errcode
        self.errmsg = errmsg

    def __str__(self):
        s = f"Error code: {self.errcode}, message: {self.errmsg}"
        return s

    def __repr__(self):
        _repr = f"{self.__class__.__name__}({self.errcode}, {self.errmsg})"
        return _repr


class ZqAuthClientException(ZqAuthException):
    """ZqAuth API client exception class"""

    def __init__(
        self, errcode, errmsg, client=None, request=None, response=None
    ):
        super().__init__(errcode, errmsg)
        self.client = client
        self.request = request
        self.response = response


class AppLoginFailedException(ZqAuthClientException):
    """ZqAuth API client app login failed"""

    def __init__(
        self, errcode, errmsg, client=None, request=None, response=None
    ):
        super().__init__(errcode, errmsg, client, request, response)


class ThirdLoginFailedException(ZqAuthClientException):
    """ZqAuth API client union id login failed"""

    def __init__(
        self, errcode, errmsg, client=None, request=None, response=None
    ):
        super().__init__(errcode, errmsg, client, request, response)


class UserNotFoundException(ZqAuthClientException):
    """ZqAuth API client user not fount"""

    def __init__(
        self, errcode, errmsg, client=None, request=None, response=None
    ):
        super().__init__(errcode, errmsg, client, request, response)


class InvalidSignatureException(ZqAuthException):
    """Invalid signature exception class"""

    def __init__(self, errcode=-40001, errmsg="Invalid signature"):
        super().__init__(errcode, errmsg)


class APILimitedException(ZqAuthClientException):
    """WeChat API call limited exception class"""

    pass
