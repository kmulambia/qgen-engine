from datetime import datetime, timezone
from uuid import UUID
from engine.models import UserModel
from engine.models.token_model import TokenModel
from engine.repositories.token_repository import TokenRepository
from engine.schemas.token_schemas import TokenData
from engine.services.base_service import BaseService
from engine.utils.jwt_util import JWTUtil
from sqlalchemy.ext.asyncio import AsyncSession


class TokenService(BaseService[TokenModel]):
    """
    TokenService is a service for managing tokens.

    Attributes:
        repository: TokenRepository

    Methods:
        generate: Generate a new token for a user.
        verify: Verify a token and return the token data.
    """

    def __init__(self):
        self.repository: TokenRepository = TokenRepository()
        super().__init__(self.repository)

    async def generate(
            self,
            db_conn: AsyncSession,
            user: UserModel,
            role_id: UUID,
            workspace_id: UUID,
            ip_address: str = None,
            user_agent: str = None
    ) -> TokenModel:
        # Generate JWT token
        token_data = TokenData(
            user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role_id=role_id,
            workspace_id=workspace_id
        )
        # Convert TokenData to dict before encoding
        jwt_token, expires_at = JWTUtil.encode_token(token_data.model_dump())

        token = TokenModel(
            jwt_token=jwt_token,
            user_id=user.id,
            token_type="bearer",
            expires_at=expires_at,
            last_ip_address=ip_address,
            user_agent=user_agent
        )

        return await self.create(db_conn, token)

    async def verify(self, db_conn: AsyncSession, jwt_token: str) -> TokenData:
        data = JWTUtil.decode_token(jwt_token)
        # Convert the expires_at string back to datetime
        expires_at = datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00'))

        token_data = TokenData(
            user_id=UUID(data["user_id"]),
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            workspace_id=UUID(data["workspace_id"]),
            role_id=UUID(data["role_id"]),
            expires_at=expires_at
        )

        if token_data.expires_at < datetime.now(timezone.utc):
            token = await self.repository.get_latest_token(db_conn, token_data.user_id)
            if not token:
                raise ValueError("Token does not exist")
            token.status = "expired"
            await self.update(db_conn, token.id, token)
            raise ValueError("Token has expired")
        return token_data
