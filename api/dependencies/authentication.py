from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from engine.services.token_service import TokenService
from engine.schemas.token_schemas import TokenData
from api.dependencies.logging import logger
from api.dependencies.db import get_db

bearer_scheme = HTTPBearer()


async def authentication(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db)
) -> TokenData:
    token_service = TokenService()
    token = credentials.credentials

    try:
        token_data = await token_service.verify(db, token)
    except Exception as e:
        logger.info(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data
