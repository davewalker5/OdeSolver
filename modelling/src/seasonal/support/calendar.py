from decimal import Decimal
from seasonal.support.numeric import D
import random


MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def circular_month_distance(a, b):
    """
    Shortest distance between two month-like values on a circular year.

    :param a: First month
    :param b: Second month
    :return: Shortest distance between the two months on a circular year
    """
    a = D(a)
    b = D(b)
    diff = abs(a - b)
    return min(diff, D("12") - diff)


def wrap_month(value):
    """
    Wrap a month-like value into the range 1..12.

    :param value: Unwrapped month number
    :return: Wrapped month number
    """
    value = D(value)

    while value < D("1"):
        value += D("12")

    while value > D("12"):
        value -= D("12")

    return value


def month_range_around(centre, padding):
    """
    Create a possibly wrapped month range around a centre month.

    :param centre: Centre month
    :param padding: Number of months either side of the centre
    :return: Wrapped month range
    """
    return wrap_month(D(centre) - D(padding)), wrap_month(D(centre) + D(padding))


def random_month_in_range(low, high):
    """
    Select a random Decimal month from a possibly wrapped range.

    :param low: Initial month number
    :param high: Final month number
    :return: Wrapped random month number in the specified range
    """
    low = D(low)
    high = D(high)

    if low <= high:
        return D(round(random.uniform(float(low), float(high)), 2))

    # Wrapped range: choose from low..12 or 1..high, weighted by length.
    late_length = D("12") - low
    early_length = high - D("1")
    total_length = late_length + early_length

    if total_length <= 0:
        return wrap_month(low)

    if D(str(random.random())) < late_length / total_length:
        return D(round(random.uniform(float(low), 12.0), 2))

    return D(round(random.uniform(1.0, float(high)), 2))


def month_is_between(month, start, end):
    """
    Test whether a month sits inside a possibly wrapped seasonal window.

    :param month: Month to test
    :param start: Season start
    :param end: Season end
    :return: True if the month is inside the window
    """
    month = D(month)
    start = D(start)
    end = D(end)

    if start <= end:
        return start <= month <= end

    return month >= start or month <= end


def month_label(value: Decimal) -> str:
    """
    Convert a month-like value to a calendar month name

    :param value: Decimal month value to round and label
    :return: Month name from ``MONTH_NAMES``
    """
    rounded = int(D(value).to_integral_value(rounding="ROUND_HALF_UP"))
    rounded = max(1, min(12, rounded))
    return MONTH_NAMES[rounded]


def rounded_month(value: Decimal) -> int:
    """
    Round a decimal month into the valid calendar month range

    :param value: Decimal month value to round
    :return: Integer month number clamped to 1..12
    """
    rounded = int(D(value).to_integral_value(rounding="ROUND_HALF_UP"))
    return max(1, min(12, rounded))
