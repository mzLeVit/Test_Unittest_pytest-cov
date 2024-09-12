import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from datetime import date
from models import Base, User, Contact
from schemas import UserCreate, ContactCreate

# Налаштування тестової бази даних
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
async def db_session():
    """Фікстура для створення тестової сесії"""
    async with engine.begin() as conn:
        # Створюємо таблиці
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        # Очищаємо таблиці після тестування
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_user(db_session):
    """Тестування створення користувача"""
    user_data = UserCreate(email="testuser@example.com", password="securepassword")
    user = User(email=user_data.email, hashed_password=user_data.password)
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).filter_by(email=user_data.email))
    saved_user = result.scalars().first()

    assert saved_user is not None
    assert saved_user.email == user_data.email


@pytest.mark.asyncio
async def test_create_contact(db_session):
    """Тестування створення контакту"""
    user = User(email="testuser@example.com", hashed_password="securepassword")
    db_session.add(user)
    await db_session.commit()

    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="123456789",
        birthday="1990-01-01",
        additional_data="Some additional info",
    )

    contact = Contact(
        first_name=contact_data.first_name,
        last_name=contact_data.last_name,
        email=contact_data.email,
        phone=contact_data.phone,
        birthday=date.fromisoformat(contact_data.birthday),
        additional_data=contact_data.additional_data,
        user_email=user.email
    )

    db_session.add(contact)
    await db_session.commit()

    result = await db_session.execute(select(Contact).filter_by(email=contact_data.email))
    saved_contact = result.scalars().first()

    assert saved_contact is not None
    assert saved_contact.email == contact_data.email
    assert saved_contact.first_name == contact_data.first_name
    assert saved_contact.last_name == contact_data.last_name


@pytest.mark.asyncio
async def test_user_relationship(db_session):
    """Тестування зв'язку між користувачем та контактами"""
    user = User(email="testuser@example.com", hashed_password="securepassword")
    db_session.add(user)
    await db_session.commit()

    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="123456789",
        birthday=date(1990, 1, 1),
        additional_data="Some additional info",
        user_email=user.email
    )

    db_session.add(contact)
    await db_session.commit()

    result = await db_session.execute(select(User).filter_by(email=user.email))
    saved_user = result.scalars().first()

    assert saved_user is not None
    assert len(saved_user.contacts) == 1
    assert saved_user.contacts[0].email == contact.email
