from datetime import datetime, timezone
import logging


def parse_date(date_str):
    if date_str is None:
        return None
    try:
        return datetime.strptime(date_str, "%d%m%Y").date()
    except ValueError:
        return None


def parse_date_iso(date_str):
    """Convert an ISO date string to a datetime object"""
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None


def format_date_iso(date):
    """Convert a datetime object to ISO format string"""
    if not date:
        return None
    if isinstance(date, str):
        return date
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")


# Function to calculate the difference between two dates
def get_datetime_difference(start_date, end_date):
    if not start_date or not end_date:
        return None

    try:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()

        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()

        difference = end_date - start_date

        return difference.days

    except ValueError:
        return None


# Function to convert date time into different units
def to_datetime_unit(difference, unit='D'):
    if not difference:
        return None
    try:
        if unit == "Y":
            return difference // 365
        elif unit == "M":
            return difference // 30
        elif unit == "W":
            return difference // 7
        else:
            return difference
    except ValueError:
        return None


# Configure basic logging (optional, but good for seeing parsing issues)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_sqlserver_datetime(value):
    """
    Safely parses a value potentially from SQL Server (datetime, string, or None)
    into a Python datetime object suitable for PostgreSQL.

    Args:
        value: The value retrieved from the database record.

    Returns:
        A datetime object, or None if the input was None or could not be parsed.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        # The driver already returned a datetime object.
        # PostgreSQL's TIMESTAMP WITHOUT TIME ZONE is common.
        # If the source datetime object is timezone-aware, you might want to remove
        # timezone info unless your target column is TIMESTAMP WITH TIME ZONE.
        if value.tzinfo is not None:
            # logging.info(f"Removing timezone info from datetime: {value}")
            return value.replace(tzinfo=None)  # Return naive datetime
        return value  # Already a naive datetime

    if isinstance(value, str):
        # It's a string, try to parse it.
        # Common SQL Server datetime formats:
        # 'YYYY-MM-DD HH:MM:SS.mmm'
        # 'YYYY-MM-DD HH:MM:SS'
        # ISO 8601 variants like 'YYYY-MM-DDTHH:MM:SS' are also possible.

        # Use datetime.fromisoformat() for robustness in Python 3.7+
        # It handles many ISO 8601 variations including microseconds and timezones.
        try:
            # fromisoformat expects 'T' separator or space. SQL Server often uses space.
            # It also handles optional timezone info. Replace 'Z' with '+00:00' for UTC.
            dt_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))

            # Again, remove timezone info if targeting TIMESTAMP WITHOUT TIME ZONE
            if dt_obj.tzinfo is not None:
                # logging.info(f"Removing timezone info after fromisoformat: {dt_obj}")
                return dt_obj.replace(tzinfo=None)
            return dt_obj

        except ValueError:
            # fromisoformat failed, try specific strptime formats as fallback
            # These formats typically represent naive datetimes
            formats_to_try = [
                '%Y-%m-%d %H:%M:%S.%f',  # With microseconds
                '%Y-%m-%d %H:%M:%S',  # Without microseconds
                # Add other formats if you know they might appear, e.g., '%m/%d/%Y'
            ]
            for fmt in formats_to_try:
                try:
                    dt_obj = datetime.strptime(value, fmt)
                    # logging.debug(f"Successfully parsed '{value}' with format '{fmt}'")
                    return dt_obj  # Found a working format

                except ValueError:
                    continue  # Try the next format

            # If none of the formats worked
            logging.warning(f"Could not parse date/datetime string: '{value}'")
            return None  # Parsing failed

    # If it's not None, datetime, or str
    logging.warning(f"Unexpected type for date/datetime value: {type(value)} for value '{value}'")
    return None  # Treat unexpected types as invalid


def parse_sqlserver_datetime_aware(value):
    """
    Safely parses a value potentially from SQL Server (datetime, string, or None)
    into a timezone-aware Python datetime object.

    If the input value/string is naive (has no timezone info), it is assumed
    to be in UTC and made timezone-aware with UTC.
    If the input value/string is already timezone-aware, its timezone is preserved.

    Args:
        value: The value retrieved from the database record.

    Returns:
        A timezone-aware datetime object, or None if the input was None
        or could not be parsed.
    """
    if value is None:
        return None

    dt_obj = None  # This will hold a datetime object if successful, could be naive or aware initially

    if isinstance(value, datetime):
        # The driver already returned a datetime object.
        # Use it directly.
        dt_obj = value

    elif isinstance(value, str):
        # It's a string, try to parse it.
        try:
            # fromisoformat expects 'T' separator or space. SQL Server often uses space.
            # It also handles optional timezone info. Replace 'Z' with '+00:00' for robustness.
            dt_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))

        except ValueError:
            # fromisoformat failed, try specific strptime formats as fallback
            # These formats typically represent naive datetimes unless format codes are used
            formats_to_try = [
                '%Y-%m-%d %H:%M:%S.%f',  # With microseconds
                '%Y-%m-%d %H:%M:%S',  # Without microseconds
                # Add other formats if you know they might appear, e.g., '%m/%d/%Y'
            ]
            for fmt in formats_to_try:
                try:
                    dt_obj = datetime.strptime(value, fmt)
                    # logging.debug(f"Successfully parsed '{value}' with format '{fmt}' using strptime")
                    break  # Stop after finding a format
                except ValueError:
                    continue  # Try next format

            if dt_obj is None:  # If loop finished without breaking
                logging.warning(f"Could not parse date/datetime string: '{value}'")
                return None  # Parsing failed completely

    else:
        # If it's not None, datetime, or str
        logging.warning(f"Unexpected type for date/datetime value: {type(value)} for value '{value}'")
        return None  # Treat unexpected types as invalid

    # --- Ensure the resulting dt_obj is timezone-aware ---
    if dt_obj is not None:
        if dt_obj.tzinfo is None:
            # The datetime object is naive (either from strptime or fromisoformat without tzinfo)
            # As requested, assume it's in UTC and make it timezone-aware with UTC
            # logging.info(f"Making naive datetime UTC aware: {dt_obj}")
            return dt_obj.replace(tzinfo=timezone.utc)
        else:
            # The datetime object is already timezone-aware.
            # We'll preserve its original timezone as it's explicitly present.
            # If you *strictly* need *all* outputs to be in the UTC zone,
            # regardless of the source timezone, uncomment the line below:
            # return dt_obj.astimezone(timezone.utc)
            # logging.debug(f"Returning already timezone-aware datetime: {dt_obj}")
            return dt_obj
    else:
        # This case should ideally not be reached if the parsing/conversion logic is sound,
        # as None is returned earlier on failure.
        logging.error("Internal error: dt_obj is None after processing.")
        return None
