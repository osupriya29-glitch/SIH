"""Authentication routes: register, login, current-user."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserRead
from app.services.user_service import authenticate_user, create_user, get_user_by_email

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={409: {"description": "Email already registered."}},
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if get_user_by_email(db, payload.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return create_user(db, email=payload.email, password=payload.password, role=payload.role)


@router.post(
    "/login",
    response_model=Token,
    summary="Log in and receive a JWT access token",
    description="Uses OAuth2 password flow — send `username` (the email) and `password` as form data.",
    responses={401: {"description": "Incorrect email or password."}},
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user_id=user.id, role=user.role.value)
    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the currently authenticated user",
)
def read_current_user(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
