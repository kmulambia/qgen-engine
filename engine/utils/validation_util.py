from datetime import datetime


# Helper function to safely convert to string
def to_str_or_none(value):
    return str(value) if value is not None else None


# Helper function to safely convert to datetime
def to_datetime_or_none(value):
    if value is None:
        return None
    # Attempt to parse known date formats, adjust as needed based on your data
    if isinstance(value, datetime):
        return value
    try:
        # Example: assuming value is a string in 'YYYY-MM-DD' format
        return datetime.strptime(str(value), '%Y-%m-%d')
    except (ValueError, TypeError):
        # Add other potential formats or handle errors as required
        return None


# Helper function to safely convert to float
def to_float_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def string_to_datetime(date_string: str, date_format: str = '%Y-%m-%d') -> datetime | None:
    """
    Converts a string representation of a date and/or time to a datetime object.

    Args:
        date_string: The string to convert.
        date_format: The expected format of the date_string (e.g., '%Y-%m-%d',
                     '%Y-%m-%d %H:%M:%S', '%m/%d/%Y'). Defaults to '%Y-%m-%d'.
                     See https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
                     for format codes.

    Returns:
        A datetime object if the conversion is successful, otherwise None.
    """
    if not isinstance(date_string, str):
        print(f"Warning: Input is not a string: {date_string}")
        return None

    try:
        # Attempt to parse the string using the specified format
        datetime_object = datetime.strptime(date_string, date_format)
        return datetime_object
    except ValueError:
        # If parsing fails, print an error and return None
        print(f"Error: Could not convert string '{date_string}' to datetime using format '{date_format}'.")
        return None
    except TypeError:
        # Handle cases where date_string might be of an unexpected type
        print(f"Error: Input '{date_string}' has an unexpected type.")
        return None
