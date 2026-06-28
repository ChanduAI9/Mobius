import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import RefreshTokenModel, UserModel
from app.infrastructure.security.jwt import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register(self, email: str, password: str, display_name: str) -> tuple[UserModel, str, str]:
        existing = await self._session.execute(select(UserModel).where(UserModel.email == email))
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        user = UserModel(
            email=email.lower(),
            password_hash=hash_password(password),
            display_name=display_name,
        )
        self._session.add(user)
        await self._session.flush()

        access_token = create_access_token(user.id, user.email)
        refresh_token, expires = create_refresh_token(user.id)
        self._session.add(
            RefreshTokenModel(user_id=user.id, token_hash=hash_token(refresh_token), expires_at=expires)
        )
        return user, access_token, refresh_token

    async def login(self, email: str, password: str) -> tuple[UserModel, str, str]:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email.lower()))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        access_token = create_access_token(user.id, user.email)
        refresh_token, expires = create_refresh_token(user.id)
        self._session.add(
            RefreshTokenModel(user_id=user.id, token_hash=hash_token(refresh_token), expires_at=expires)
        )
        return user, access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        from app.infrastructure.security.jwt import decode_token

        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        user_id = uuid.UUID(payload["sub"])
        result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        access_token = create_access_token(user.id, user.email)
        new_refresh, expires = create_refresh_token(user.id)
        self._session.add(
            RefreshTokenModel(user_id=user.id, token_hash=hash_token(new_refresh), expires_at=expires)
        )
        return access_token, new_refresh

    async def get_user(self, user_id: uuid.UUID) -> UserModel | None:
        result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalar_one_or_none()
