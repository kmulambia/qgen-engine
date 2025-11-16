from fastapi import HTTPException, status
from api.dependencies.logging import logger


class ErrorHandling:
    """Simple error handling class for API responses"""

    @staticmethod
    def invalid_credentials(detail: str = "Invalid credentials") -> HTTPException:
        logger.error(f"Authentication error: {detail}")
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

    @staticmethod
    def permission_denied(detail: str = "Permission denied") -> HTTPException:
        logger.error(f"Authorization error: {detail}")
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

    @staticmethod
    def not_found(detail: str = "Resource not found") -> HTTPException:
        logger.error(f"Not found error: {detail}")
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

    @staticmethod
    def already_exists(detail: str = "Resource already exists") -> HTTPException:
        logger.error(f"Conflict error: {detail}")
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

    @staticmethod
    def validation_error(detail: str = "Validation error") -> HTTPException:
        logger.error(f"Validation error: {detail}")
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

    @staticmethod
    def server_error(detail: str = "Internal server error") -> HTTPException:
        logger.error(f"Server error: {detail}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

    @staticmethod
    def bad_request(detail: str = "Bad request") -> HTTPException:
        logger.error(f"Bad request error: {detail}")
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    @staticmethod
    def unauthorized(detail: str = "Unauthorized") -> HTTPException:
        logger.error(f"Unauthorized error: {detail}")
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

    @staticmethod
    def forbidden(detail: str = "Forbidden") -> HTTPException:
        logger.error(f"Forbidden error: {detail}")
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

    @staticmethod
    def conflict(detail: str = "Conflict") -> HTTPException:
        logger.error(f"Conflict error: {detail}")
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

    @classmethod
    def invalid_request(cls, param):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(param)
        )
