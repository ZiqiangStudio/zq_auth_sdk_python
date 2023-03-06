import logging

from zq_auth_sdk.client import ZqAuthClient  # noqa
from zq_auth_sdk.exceptions import (  # noqa
    APILimitedException,
    AppLoginFailedException,
    ThirdLoginFailedException,
    UserNotFoundException,
    ZqAuthClientException,
    ZqAuthException,
)

__version__ = "0.1.0"
__author__ = "Nagico"

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())
