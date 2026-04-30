from enum import IntEnum


class OptionReason(IntEnum):
    """
    Validation reason codes
    """
    OK = 0,
    EMPTY = 1,
    VALUE_ERROR = 2
