from typing import Dict, List, TypedDict, Union

JSONVal = Union[
    None, bool, str, float, int, List["JSONVal"], Dict[str, "JSONVal"]
]


class ZqAuthResponseData(TypedDict, total=True):
    code: str
    detail: str
    msg: str
    data: JSONVal
