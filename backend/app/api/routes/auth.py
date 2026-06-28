import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import LoginRequest, RefreshRequest, RegisterRequest
from app.application.auth.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user_id, rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    auth: AuthService = Depends(get_auth_service),
    _: None = Depends(rate_limit),
):
    try:
        user, access_token, refresh_token = await auth.register(
            body.email, body.password, body.display_name
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login")
async def login(
    body: LoginRequest,
    auth: AuthService = Depends(get_auth_service),
    _: None = Depends(rate_limit),
):
    try:
        user, access_token, refresh_token = await auth.login(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh(body: RefreshRequest, auth: AuthService = Depends(get_auth_service)):
    try:
        access_token, refresh_token = await auth.refresh(body.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/me")
async def me(
    user_id: uuid.UUID = Depends(get_current_user_id),
    auth: AuthService = Depends(get_auth_service),
):
    user = await auth.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "preferences": user.preferences or {},
        "created_at": user.created_at.isoformat(),
    }
