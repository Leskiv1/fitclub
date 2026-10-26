"""Authentication: sign in, client self-registration, current user."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep, CurrentUser
from app.api.errors import ERROR_RESPONSES
from app.schemas.auth import CurrentUserRead, LoginRequest, TokenResponse
from app.schemas.clients import ClientCreate

router = APIRouter(prefix="/auth", tags=["Авторизація"], responses=ERROR_RESPONSES)


@router.post("/login", summary="Увійти: отримати токен доступу")
def login(data: LoginRequest, auth: AuthServiceDep) -> TokenResponse:
    user, token, expires_in = auth.login(data.email, data.password)
    return TokenResponse(access_token=token, expires_in=expires_in, user=CurrentUserRead.from_model(user))


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Зареєструватися як клієнт")
def register(data: ClientCreate, auth: AuthServiceDep) -> TokenResponse:
    client, token, expires_in = auth.register_client(data)
    return TokenResponse(
        access_token=token, expires_in=expires_in, user=CurrentUserRead.from_model(client.user)
    )


@router.get("/me", summary="Поточний користувач")
def me(user: CurrentUser) -> CurrentUserRead:
    return CurrentUserRead.from_model(user)
