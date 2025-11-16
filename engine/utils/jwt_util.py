from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError
from engine.utils.config_util import load_config
from uuid import UUID

config = load_config()
if not config:
    raise ValueError("JWT Environment configuration not found")


class JWTUtil:
    JWT_SECRET_KEY = config.require_variable("KEY")
    JWT_ALGORITHM = config.get_variable("ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(config.get_variable("TOKEN_EXPIRE_MINUTES", "30"))

    @classmethod
    def encode_token(
            cls,
            data: dict,
            expires_delta: timedelta = None
    ) -> tuple[str, datetime]:
        """
        Create a JWT token from a dictionary of data

        Args:
            data (dict): Dictionary of claims to encode in the token
            expires_delta (timedelta, optional): Custom expiration time

        Returns:
            tuple[str, datetime]: Encoded JWT token and its expiration time
        """
        # Create a copy to avoid modifying the original dictionary
        to_encode = data.copy()

        # Remove None values
        to_encode = {k: v for k, v in to_encode.items() if v is not None}

        # Convert UUID objects to strings
        for key, value in to_encode.items():
            if isinstance(value, UUID):
                to_encode[key] = str(value)

        # Add expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=cls.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode["expires_at"] = expire.isoformat()

        # Encode token
        encoded_jwt = jwt.encode(
            to_encode,
            cls.JWT_SECRET_KEY,
            algorithm=cls.JWT_ALGORITHM
        )

        return encoded_jwt, expire

    @classmethod
    def decode_token(cls, token: str) -> dict:
        """
        Decode and verify a JWT token

        Args:
            token (str): JWT token to decode

        Returns:
            dict: Decoded payload

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                cls.JWT_SECRET_KEY,
                algorithms=[cls.JWT_ALGORITHM]
            )
            return payload
        except ExpiredSignatureError:
            raise ValueError("Token has expired")
        except PyJWTError:
            raise ValueError("Invalid token")

    @classmethod
    def verify_token(cls, token: str) -> bool:
        """
        Verify if a token is valid

        Args:
            token (str): JWT token to verify

        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            cls.decode_token(token)
            return True
        except (ExpiredSignatureError, PyJWTError):
            return False
