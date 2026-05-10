from datetime import datetime


def print_message(message):
    """
    Show a timestamped message

    :param message: Message text
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} : {message}")


def print_error(message):
    """
    Show a timestamped error message

    :param message: Message text
    """
    print_message(f"ERROR: {message}")
