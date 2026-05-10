from argparse import Namespace
from pathlib import Path
from typing import Any, Mapping


def print_args_table(args: Namespace, title: str = "Arguments") -> None:
    """
    Pretty-print argparse arguments as a console table

    :param args: argparse arguments
    :param title: Table title
    """
    print_dict_table(vars(args), title=title)


def print_dict_table(
    values: Mapping[str, Any],
    title: str = "Values",
    key_header: str = "Option",
    value_header: str = "Value",
    sort_keys: bool = True
) -> None:
    """
    Pretty-print a dictionary-like object as a console table

    :param values: Dictionary of values
    :param title: Table title
    :param key_header: Column header for the keys column
    :param value_header: Column header for the values column
    :param sort_keys: If true, sort before tabulating
    """

    table_rows = build_dict_table(values, title, key_header, value_header, sort_keys)
    for row in table_rows:
        print(row)


def build_dict_table(
    values: Mapping[str, Any],
    title: str = "Values",
    key_header: str = "Option",
    value_header: str = "Value",
    sort_keys: bool = True
) -> None:
    """
    Build a text-based table from a dictionary-like object

    :param values: Dictionary of values
    :param title: Table title
    :param key_header: Column header for the keys column
    :param value_header: Column header for the values column
    :param sort_keys: If true, sort before tabulating
    :return: List of strings representing rows in the output
    """

    table_rows = []

    items = values.items()

    if sort_keys:
        items = sorted(items)

    rows = [
        (str(key), format_value(value))
        for key, value in items
    ]

    key_width = max(len(key_header), max(len(k) for k, _ in rows))
    value_width = max(len(value_header), max(len(v) for _, v in rows))

    border = (
        "+"
        + "-" * (key_width + 2)
        + "+"
        + "-" * (value_width + 2)
        + "+"
    )

    table_width = len(border)

    if len(title) < table_width:
        table_rows.append(f"\n{title.center(table_width)}")
    else:
        table_rows.append(f"\n{title}")

    table_rows.append(border)
    table_rows.append(
        f"| {key_header.ljust(key_width)} "
        f"| {value_header.ljust(value_width)} |"
    )
    table_rows.append(border)

    for key, value in rows:
        table_rows.append(
            f"| {key.ljust(key_width)} "
            f"| {value.ljust(value_width)} |"
        )

    table_rows.append(border)

    return table_rows


def format_value(value: Any) -> str:
    """
    Convert value into a readable strings

    :param value: The value to convert
    """

    if value is None:
        return "None"

    if isinstance(value, bool):
        return "True" if value else "False"

    if isinstance(value, (list, tuple, set)):
        return ", ".join(format_value(v) for v in value)

    if isinstance(value, Path):
        return value.name

    if isinstance(value, str):
        if "/" in value or "\\" in value:
            return Path(value).name

    return str(value)
