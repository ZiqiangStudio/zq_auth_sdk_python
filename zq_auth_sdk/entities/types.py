JSONVal = (
    type(None)
    | bool
    | str
    | float
    | int
    | list["JSONVal"]
    | dict[str, "JSONVal"]
)
