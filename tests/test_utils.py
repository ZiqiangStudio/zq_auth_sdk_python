import os

import pytest

from zq_auth_sdk.utils import (
    ObjectDict,
    check_request_signature,
    check_signature,
    rsa_decrypt,
    rsa_encrypt,
)

_TESTS_PATH = os.path.abspath(os.path.dirname(__file__))
_CERTS_PATH = os.path.join(_TESTS_PATH, "certs")


def skip_if_no_cryptography():
    try:
        import cryptography  # NOQA

        return False
    except ImportError:
        return True


def test_object_dict():
    obj = ObjectDict()
    assert obj.xxx is None
    obj.xxx = 1
    assert 1 == obj.xxx


def test_check_signature_should_ok():
    token = "test"
    signature = "f21891de399b4e33a1a93c9a7b8a8fffb5a443ff"
    timestamp = "1410685589"
    nonce = "test"
    check_signature(token, signature, timestamp, nonce)


def test_check_signature_should_fail():
    from zq_auth_sdk.exceptions import InvalidSignatureException

    token = "test"
    signature = "f21891de399b4e33a1a93c9a7b8a8fffb5a443fe"
    timestamp = "1410685589"
    nonce = "test"

    with pytest.raises(InvalidSignatureException):
        check_signature(token, signature, timestamp, nonce)


def test_check_wxa_signature():
    from zq_auth_sdk.exceptions import InvalidSignatureException

    # 微信官方示例
    raw_data = '{"nickName":"Band","gender":1,"language":"zh_CN","city":"Guangzhou","province":"Guangdong","country":"CN","avatarUrl":"http://wx.qlogo.cn/mmopen/vi_32/1vZvI39NWFQ9XM4LtQpFrQJ1xlgZxx3w7bQxKARol6503Iuswjjn6nIGBiaycAjAtpujxyzYsrztuuICqIM5ibXQ/0"}'  # noqa
    session_key = "HyVFkGl5F5OQWJZZaNzBBg=="
    client_signature = "75e81ceda165f4ffa64f4068af58c64b8f54b88c"
    check_request_signature(session_key, raw_data, client_signature)

    client_signature = "fake_sign"

    with pytest.raises(InvalidSignatureException):
        check_request_signature(session_key, raw_data, client_signature)

    # 带中文的示例
    raw_data = '{"nickName":"Xavier-Lam林","gender":1,"language":"zh_CN","city":"Ningde","province":"Fujian","country":"China","avatarUrl":"https://wx.qlogo.cn/mmopen/vi_32/vTxUxcbjcZ8t9eU6YfXBwRU89KS9uRILEDro01MTYp7UKYsyTjLFMIVhB0AlBuEvLHbhmO3OpaHw5zwlSetuLg/132"}'  # noqa
    session_key = "GtYYez5b/M5HhT4L7n31gQ=="
    client_signature = "8fde625b7640734a13c071c05d792b5cef21cf89"
    check_request_signature(session_key, raw_data, client_signature)


def test_wechat_card_signer():
    from zq_auth_sdk.utils import ZqAuthSigner

    signer = ZqAuthSigner()
    signer.add_data("789")
    signer.add_data("456")
    signer.add_data("123")
    signature = signer.signature

    assert "f7c3bc1d808e04732adf679965ccc34ca7ae3441" == signature


@pytest.mark.skipif(
    skip_if_no_cryptography(), reason="cryptography not installed"
)
def test_rsa_encrypt_decrypt():
    target_string = "hello world"
    with open(
        os.path.join(_CERTS_PATH, "rsa_public_key.pem"), "rb"
    ) as public_fp, open(
        os.path.join(_CERTS_PATH, "rsa_private_key.pem"), "rb"
    ) as private_fp:
        encrypted_string = rsa_encrypt(
            target_string, public_fp.read(), b64_encode=False
        )
        assert rsa_decrypt(
            encrypted_string, private_fp.read()
        ) == target_string.encode("utf-8")
