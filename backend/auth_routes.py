from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.auth_models import (
    UserCreate,
    UserLogin,
    TokenResponse,
    UserResponse
)

from backend.user_auth import (
    create_user,
    authenticate_user
)

from backend.auth import create_access_token

from backend.dependencies import get_current_user


# ============================================================
# AUTHENTICATION ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


# ============================================================
# REGISTER USER
# ============================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(user: UserCreate):

    try:

        created_user = create_user(
            username=user.username,
            password=user.password,
            role=user.role
        )

        return created_user

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================
# LOGIN USER - JSON LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(user: UserLogin):

    authenticated_user = authenticate_user(
        username=user.username,
        password=user.password
    )

    if not authenticated_user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        user_id=authenticated_user["user_id"],
        username=authenticated_user["username"],
        role=authenticated_user["role"]
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ============================================================
# OAUTH2 TOKEN LOGIN
# ============================================================

@router.post(
    "/token",
    response_model=TokenResponse
)
def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    authenticated_user = authenticate_user(
        username=form_data.username,
        password=form_data.password
    )

    if not authenticated_user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        user_id=authenticated_user["user_id"],
        username=authenticated_user["username"],
        role=authenticated_user["role"]
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ============================================================
# GET CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user=Depends(get_current_user)
):

    return current_user