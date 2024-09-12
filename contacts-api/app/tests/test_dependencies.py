import pytest
from unittest.mock import AsyncMock, patch
from fastapi_mail import FastMail, MessageSchema
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url

from app.email import send_verification_email, upload_avatar, send_reset_email

@pytest.mark.asyncio
@patch('app.email.FastMail')
@patch('app.email.MessageSchema')
async def test_send_verification_email(mock_MessageSchema, mock_FastMail):
    # Мокування
    mock_fm_instance = AsyncMock()
    mock_FastMail.return_value = mock_fm_instance

    email = 'test@example.com'
    token = 'fake_token'

    # Визначення результатів моків
    mock_MessageSchema.return_value = mock_MessageSchema(
        subject="Email Verification",
        recipients=[email],
        body=f"To verify your email, click the following link: http://your-app-url.com/verify-email?token={token}",
        subtype="html"
    )

    await send_verification_email(email, token)

    # Перевірка, чи був викликаний метод send_message
    mock_fm_instance.send_message.assert_called_once_with(mock_MessageSchema.return_value)

@pytest.mark.asyncio
@patch('app.email.upload')
@patch('app.email.cloudinary_url')
async def test_upload_avatar(mock_cloudinary_url, mock_upload):
    # Мокування
    mock_upload.return_value = {'public_id': 'fake_id'}
    mock_cloudinary_url.return_value = ('http://res.cloudinary.com/your-cloud-name/image/upload/fake_id.jpg', {})

    file = AsyncMock()
    file.file = 'path/to/file'

    avatar_url = await upload_avatar(file)

    # Перевірка результатів
    mock_upload.assert_called_once_with('path/to/file')
    mock_cloudinary_url.assert_called_once_with('fake_id', format="jpg")
    assert avatar_url == 'http://res.cloudinary.com/your-cloud-name/image/upload/fake_id.jpg'

@pytest.mark.asyncio
@patch('app.email.FastMail')
@patch('app.email.MessageSchema')
async def test_send_reset_email(mock_MessageSchema, mock_FastMail):
    # Мокування
    mock_fm_instance = AsyncMock()
    mock_FastMail.return_value = mock_fm_instance

    email = 'test@example.com'
    token = 'fake_token'

    # Визначення результатів моків
    mock_MessageSchema.return_value = mock_MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=f"To reset your password, click the following link: http://your-app-url.com/reset-password?token={token}",
        subtype="html"
    )

    await send_reset_email(email, token)

    # Перевірка, чи був викликаний метод send_message
    mock_fm_instance.send_message.assert_called_once_with(mock_MessageSchema.return_value)
