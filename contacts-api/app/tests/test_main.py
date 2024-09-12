import unittest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, create_access_token, SECRET_KEY
from models import Base, User
from schemas import UserCreate
import jwt
import datetime

# Налаштування для тестування
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# Ініціалізація клієнта FastAPI
client = TestClient(app)

# Фікстури для тестування
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestMain(unittest.TestCase):

    @classmethod
    async def setUpClass(cls):
        """Ініціалізація перед запуском всіх тестів"""
        async with engine.begin() as conn:
            # Створюємо таблиці в базі даних
            await conn.run_sync(Base.metadata.create_all)

    async def setUp(self):
        """Ініціалізація перед кожним тестом"""
        async with TestingSessionLocal() as db:
            # Очищаємо базу даних
            await db.execute("DELETE FROM user")
            await db.commit()

    async def test_register_user(self):
        """Тестування реєстрації користувача"""
        response = client.post("/register", json={"email": "test@example.com", "password": "testpassword"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("msg", response.json())
        self.assertEqual(response.json()["msg"], "User created. Please verify your email.")

    async def test_login_user(self):
        """Тестування авторизації користувача"""
        # Спочатку реєструємо користувача
        client.post("/register", json={"email": "test@example.com", "password": "testpassword"})
        # Потім авторизуємося
        response = client.post("/token", data={"username": "test@example.com", "password": "testpassword"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        self.assertIn("refresh_token", response.json())

    async def test_password_reset_request(self):
        """Тестування запиту на скидання паролю"""
        client.post("/register", json={"email": "test@example.com", "password": "testpassword"})
        response = client.post("/password/reset/request", json={"email": "test@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("msg", response.json())
        self.assertEqual(response.json()["msg"], "Password reset email sent")

    async def test_reset_password(self):
        """Тестування скидання паролю"""
        client.post("/register", json={"email": "test@example.com", "password": "testpassword"})
        reset_token = create_access_token({"sub": "test@example.com"}, expires_delta=datetime.timedelta(minutes=15))
        response = client.post("/reset-password", json={"email": "test@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("msg", response.json())
        self.assertEqual(response.json()["msg"], "Password reset link sent to your email.")

    async def test_update_avatar(self):
        """Тестування оновлення аватара"""
        client.post("/register", json={"email": "test@example.com", "password": "testpassword"})
        login_response = client.post("/token", data={"username": "test@example.com", "password": "testpassword"})
        access_token = login_response.json()["access_token"]
        with open("test_avatar.png", "wb") as f:
            f.write(b"dummy avatar data")
        with open("test_avatar.png", "rb") as f:
            response = client.post("/users/me/avatar", files={"file": ("test_avatar.png", f, "image/png")}, headers={"Authorization": f"Bearer {access_token}"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("avatar_url", response.json())

    @classmethod
    async def tearDownClass(cls):
        """Очищення після запуску всіх тестів"""
        async with engine.begin() as conn:
            # Видаляємо таблиці з бази даних
            await conn.run_sync(Base.metadata.drop_all)

if __name__ == "__main__":
    unittest.main()
