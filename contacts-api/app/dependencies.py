from fastapi_mail import FastMail, MessageSchema
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url


# Функція для відправлення листа з верифікацією
async def send_verification_email(email: str, token: str):
    verification_link = f"http://your-app-url.com/verify-email?token={token}"

    message = MessageSchema(
        subject="Email Verification",
        recipients=[email],
        body=f"To verify your email, click the following link: {verification_link}",
        subtype="html"
    )

    fm = FastMail()  # Ініціалізуйте FastMail з вашими налаштуваннями
    await fm.send_message(message)


# Функція для завантаження аватара
async def upload_avatar(file):
    result = upload(file.file)
    avatar_url, options = cloudinary_url(result['public_id'], format="jpg")
    return avatar_url


# Функція для відправлення листа з скиданням пароля
async def send_reset_email(email: str, token: str):
    reset_link = f"http://your-app-url.com/reset-password?token={token}"

    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=f"To reset your password, click the following link: {reset_link}",
        subtype="html"
    )

    fm = FastMail()  # Ініціалізуйте FastMail з вашими налаштуваннями
    await fm.send_message(message)
