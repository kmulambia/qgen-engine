import random
import string
import time


def generate_random_string(length: int) -> str:
    """Generate a random string of specified length."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def generate_timestamp_string() -> str:
    """
    Generate a Unix timestamp string
    Returns:
        String representation of Unix timestamp in milliseconds
    """
    return str(int(time.time() * 1000))
