"""
    wechatpy.utils
    ~~~~~~~~~~~~~~~

    本模块提供了一些工具函数和类。
"""

import base64
import copy
import hashlib
import hmac
import logging
import random
import string

logger = logging.getLogger(__name__)


class ObjectDict(dict):
    """Makes a dictionary behave like an object, with attribute-style access."""

    def __getattr__(self, key):
        if key in self:
            return self[key]
        return None

    def __setattr__(self, key, value):
        self[key] = value


class ZqAuthSigner:
    """ZqAuth data signer"""

    def __init__(self, delimiter=b""):
        self._data = []
        self._delimiter = to_binary(delimiter)

    def add_data(self, *args):
        """Add data to signer"""
        for data in args:
            self._data.append(to_binary(data))

    @property
    def signature(self):
        """Get data signature"""
        self._data.sort()
        str_to_sign = self._delimiter.join(self._data)
        return hashlib.sha1(str_to_sign).hexdigest()


def check_signature(token, signature, timestamp, nonce):
    """Check ZqAuth callback signature, raises InvalidSignatureException
    if check failed.

    :param token: ZqAuth callback token
    :param signature: ZqAuth callback signature sent by ZqAuth server
    :param timestamp: ZqAuth callback timestamp sent by ZqAuth server
    :param nonce: ZqAuth callback nonce sent by ZqAuth sever
    """
    signer = ZqAuthSigner()
    signer.add_data(token, timestamp, nonce)
    if signer.signature != signature:
        from zq_auth_sdk.exceptions import InvalidSignatureException

        raise InvalidSignatureException()


def check_request_signature(session_key, raw_data, client_signature):
    """校验前端传来的rawData签名正确
    详情请参考
    https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/signature.html # noqa

    :param session_key: code换取的session_key
    :param raw_data: 前端拿到的rawData
    :param client_signature: 前端拿到的signature
    :raises: InvalidSignatureException
    :return: 返回数据dict
    """
    str2sign = (raw_data + session_key).encode("utf-8")
    signature = hashlib.sha1(str2sign).hexdigest()
    if signature != client_signature:
        from zq_auth_sdk.exceptions import InvalidSignatureException

        raise InvalidSignatureException()


def to_text(value, encoding="utf-8"):
    """Convert value to unicode, default encoding is utf-8

    :param value: Value to be converted
    :param encoding: Desired encoding
    """
    if not value:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode(encoding)
    return str(value)


def to_binary(value, encoding="utf-8"):
    """Convert value to binary string, default encoding is utf-8

    :param value: Value to be converted
    :param encoding: Desired encoding
    """
    if not value:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode(encoding)
    return to_text(value).encode(encoding)


def random_string(length=16):
    rule = string.ascii_letters + string.digits
    rand_list = random.sample(rule, length)
    return "".join(rand_list)


def now(tz=None):
    """
    获取当前aware时间
    :return:
    """
    import datetime

    if tz:
        return datetime.datetime.now(tz)
    return datetime.datetime.now().astimezone()


def format_url(params, api_key=None):
    data = [to_binary(f"{k}={params[k]}") for k in sorted(params) if params[k]]
    if api_key:
        data.append(to_binary(f"key={api_key}"))
    return b"&".join(data)


def calculate_signature(params, api_key):
    url = format_url(params, api_key)
    logger.debug("Calculate Signature URL: %s", url)
    return to_text(hashlib.md5(url).hexdigest().upper())


def calculate_signature_hmac(params, api_key):
    url = format_url(params, api_key)
    sign = to_text(
        hmac.new(api_key.encode(), msg=url, digestmod=hashlib.sha256)
        .hexdigest()
        .upper()
    )
    return sign


def _check_signature(params, api_key):
    _params = copy.deepcopy(params)
    sign = _params.pop("sign", "")
    return sign == calculate_signature(_params, api_key)


def rsa_encrypt(data, pem, b64_encode=True):
    """
    rsa 加密
    :param data: 待加密字符串/binary
    :param pem: RSA public key 内容/binary
    :param b64_encode: 是否对输出进行 base64 encode
    :return: 如果 b64_encode=True 的话，返回加密并 base64 处理后的 string；否则返回加密后的 binary
    """
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    encoded_data = to_binary(data)
    pem = to_binary(pem)
    public_key = serialization.load_pem_public_key(pem)
    encrypted_data = public_key.encrypt(
        encoded_data,
        padding=padding.OAEP(
            mgf=padding.MGF1(hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None,
        ),
    )
    if b64_encode:
        encrypted_data = base64.b64encode(encrypted_data).decode("utf-8")
    return encrypted_data


def rsa_decrypt(encrypted_data, pem, password=None):
    """
    rsa 解密
    :param encrypted_data: 待解密 bytes
    :param pem: RSA private key 内容/binary
    :param password: RSA private key pass phrase
    :return: 解密后的 binary
    """
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    encrypted_data = to_binary(encrypted_data)
    pem = to_binary(pem)
    private_key = serialization.load_pem_private_key(pem, password)
    data = private_key.decrypt(
        encrypted_data,
        padding=padding.OAEP(
            mgf=padding.MGF1(hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None,
        ),
    )
    return data
