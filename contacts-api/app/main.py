from fastapi import FastAPI, Depends, HTTPException, status, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from pydantic import EmailStr
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from redis import asyncio as aioredis
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import jwt
import datetime
import os
from models import Base, User, Contact
from schemas import UserCreate, ContactCreate
from database import get_db
from dependencies import send_verification_email, upload_avatar, send_reset_email



# Налаштування конфігурації
SECRET_KEY = os.getenv("SECRET_KEY", "9smP3~7sMg4kCVfUFc&2!t7;3(LU4")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Ініціалізація FastAPI
app = FastAPI()

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Хешування паролів
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, limiter._rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Підключення до Redis для кешування
@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

# Функції для створення токенів
def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

# Реєстрація користувача
@app.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        existing_user = await db.execute(select(User).filter(User.email == user.email))
        if existing_user.scalars().first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        hashed_password = pwd_context.hash(user.password)
        new_user = User(email=user.email, hashed_password=hashed_password)
        db.add(new_user)
        await db.commit()

        # Відправка електронного листа для верифікації
        token = create_access_token({"sub": new_user.email})
        await send_verification_email(EmailStr(email=new_user.email), token)

        return {"msg": "User created. Please verify your email."}

# Авторизація користувача з кешуванням у Redis
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    async with db.begin():
        user = await db.execute(select(User).filter(User.email == form_data.username))
        user = user.scalars().first()
        if not user or not pwd_context.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

        access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data={"sub": user.email})

        # Кешування поточного користувача в Redis
        redis_client = FastAPICache.get_backend().redis
        await redis_client.set(f"user:{user.email}", user.email, ex=60 * 60)  # зберігається на 1 годину

        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# Запит на скидання паролю
@app.post("/password/reset/request")
async def request_password_reset(email: EmailStr, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        user = await db.execute(select(User).filter(User.email == email))
        user = user.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Генерація токену для скидання паролю
        reset_token = create_access_token(data={"sub": user.email})
        background_tasks.add_task(send_reset_email, email, reset_token)
        return {"msg": "Password reset email sent"}

# Скидання паролю
@app.post("/reset-password")
async def reset_password(email: EmailStr, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        user = await db.execute(select(User).filter(User.email == email))
        user = user.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Генерація токену для скидання паролю
        reset_token = create_access_token(data={"sub": user.email}, expires_delta=datetime.timedelta(minutes=15))

        # Відправка листа зі скиданням паролю
        await send_verification_email(email, reset_token)

        return {"msg": "Password reset link sent to your email."}


# Оновлення аватара користувача
@app.post("/users/me/avatar")
async def update_avatar(file: UploadFile, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    avatar_url = await upload_avatar(file)
    async with db.begin():
        user = await db.execute(select(User).filter(User.email == payload["sub"]))
        user = user.scalars().first()
        user.avatar_url = avatar_url
        db.commit()
        return {"avatar_url": avatar_url}
