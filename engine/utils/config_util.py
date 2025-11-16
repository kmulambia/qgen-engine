import os
from pathlib import Path
from functools import lru_cache
from typing import Optional, Union, Any
from dotenv import load_dotenv


class EnvConfigError(Exception):
    """Custom exception for environment configuration errors"""
    pass


class EnvConfig:
    """
    Simple environment configuration manager.
    Handles .env file loading and variable access with type casting.
    """

    def __init__(self, env_path: Optional[Union[str, Path]] = None):
        """
        Initialize environment configuration.

        Args:
            env_path: Path to .env file (optional)
        """
        self._load_env_file(env_path)

    @staticmethod
    def _load_env_file(env_path: Optional[Union[str, Path]] = None) -> None:
        """
        Load environment variables from .env file.

        Args:
            env_path: Path to .env file (optional)
        """
        if env_path:
            env_file = Path(env_path)
        else:
            env_file = Path('.env')

        if env_file.exists():
            load_dotenv(env_file)
        else:
            raise EnvConfigError(f"Environment file not found: {env_file}")

    @staticmethod
    def get_variable(
            key: str,
            default: Any = None,
            cast_type: type = str,
            required: bool = False
    ) -> Any:
        """
        Get environment variable with type casting.

        Args:
            key: Environment variable name
            default: Default value if not found
            cast_type: Type to cast the value to
            required: Whether the variable is required

        Returns:
            Environment variable value cast to specified type

        Raises:
            EnvConfigError: If a required variable is missing
        """
        value = os.getenv(key)

        if value is None:
            if required:
                raise EnvConfigError(f"Required environment variable missing: {key}")
            return default

        try:
            if cast_type == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            if cast_type == list:
                return [item.strip() for item in value.split(',')]

            return cast_type(value)
        except (ValueError, TypeError) as e:
            raise EnvConfigError(
                f"Failed to cast {key} to {cast_type.__name__}: {str(e)}"
            )

    def require_variable(
            self,
            key: str,
            cast_type: type = str
    ) -> Any:
        """
        Get a required environment variable.

        Args:
            key: Environment variable name
            cast_type: Type to cast the value to

        Returns:
            Environment variable value cast to specified type

        Raises:
            EnvConfigError: If the variable is missing
        """
        return self.get_variable(key, cast_type=cast_type, required=True)


@lru_cache()
def load_config(env_path: Optional[Union[str, Path]] = None) -> EnvConfig:
    """
    Get or create environment configuration.

    Args:
        env_path: Path to .env file (optional)

    Returns:
        EnvConfig instance

    Example:
        >>> env = load_config()
        >>> debug = env.get_variable("DEBUG", False, bool)
        >>> port = env.require_variable("PORT", int)
    """
    return EnvConfig(env_path)
