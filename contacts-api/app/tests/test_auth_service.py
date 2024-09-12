import unittest
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from your_module import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)

class TestAuthService(unittest.TestCase):

    def setUp(self):
        """Ініціалізація перед кожним тестом"""
        self.password = "testpassword"
        self.hashed_password = hash_password(self.password)
        self.data = {"email": "test@example.com"}
        self.access_token = create_access_token(self.data)
        self.refresh_token = create_refresh_token(self.data)

    def test_hash_password(self):
        """Тестування хешування пароля"""
        self.assertTrue(verify_password(self.password, self.hashed_password))
        self.assertFalse(verify_password("wrongpassword", self.hashed_password))

    def test_create_access_token(self):
        """Тестування створення токену доступу"""
        payload = verify_token(self.access_token)
        self.assertEqual(payload["email"], self.data["email"])
        # Перевірка терміну дії токену
        expire = datetime.utcfromtimestamp(payload["exp"])
        self.assertTrue(expire > datetime.utcnow())
        self.assertTrue(expire <= datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    def test_create_refresh_token(self):
        """Тестування створення токену оновлення"""
        payload = verify_token(self.refresh_token)
        self.assertEqual(payload["email"], self.data["email"])
        # Перевірка терміну дії токену
        expire = datetime.utcfromtimestamp(payload["exp"])
        self.assertTrue(expire > datetime.utcnow())
        self.assertTrue(expire <= datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    def test_verify_token(self):
        """Тестування перевірки токену"""
        payload = verify_token(self.access_token)
        self.assertEqual(payload["email"], self.data["email"])
        self.assertTrue("exp" in payload)

        # Перевірка токену з неправильним секретним ключем
        invalid_token = self.access_token + "invalid"
        self.assertEqual(verify_token(invalid_token), {})

if __name__ == '__main__':
    unittest.main()
