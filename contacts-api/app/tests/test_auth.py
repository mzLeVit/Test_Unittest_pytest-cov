import unittest
from app.auth import authenticate_user


class TestAuth(unittest.TestCase):

    def test_authenticate_user_success(self):
        """Тестування успішної аутентифікації"""
        self.assertTrue(authenticate_user("admin", "password123"))

    def test_authenticate_user_failure(self):
        """Тестування невдалої аутентифікації з неправильним паролем"""
        self.assertFalse(authenticate_user("admin", "wrongpassword"))

    def test_authenticate_user_no_user(self):
        """Тестування невдалої аутентифікації з неправильним ім'ям користувача"""
        self.assertFalse(authenticate_user("wronguser", "password123"))


if __name__ == '__main__':
    unittest.main()
