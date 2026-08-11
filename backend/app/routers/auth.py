# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut, MarketplaceCredentials
from app.security import hash_password, verify_password, create_access_token, encrypt_secret, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")



async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    try:
        user_id = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Fetch profile info of the currently logged-in user."""
    return current_user


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_email = await db.execute(select(User).where(User.email == payload.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.username:
        existing_username = await db.execute(select(User).where(User.username == payload.username))
        if existing_username.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        username=payload.username,
        age=payload.age,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Support logging in with either email or username
    result = await db.execute(
        select(User).where((User.email == form_data.username) | (User.username == form_data.username))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    from datetime import datetime, timezone
    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(user)
    await db.commit()

    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/marketplace-credentials", status_code=status.HTTP_204_NO_CONTENT)
async def submit_marketplace_credentials(
    payload: MarketplaceCredentials,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Client submits official Eldorado Seller API credentials (client_id, client_secret). Stored encrypted, never logged."""
    if payload.client_secret:
        current_user.marketplace_client_id = payload.client_id
        current_user.marketplace_client_secret_encrypted = encrypt_secret(payload.client_secret)
    elif payload.api_key:
        current_user.marketplace_api_key_encrypted = encrypt_secret(payload.api_key)
    else:
        raise HTTPException(status_code=400, detail="Must provide client_id & client_secret or api_key")

    db.add(current_user)
    await db.commit()

