import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.future import select
from app.models import Contact
from app.schemas import ContactCreate, ContactUpdate
from app.crud import get_contact, get_contacts, create_contact, update_contact, delete_contact


@pytest.mark.asyncio
@patch('app.crud.get_contact')
async def test_get_contact(mock_get_contact):
    # Мокування
    mock_db_session = AsyncMock()
    mock_contact = MagicMock(Contact)
    mock_get_contact.return_value = mock_contact

    result = await get_contact(mock_db_session, 1)

    # Перевірка результату
    assert result == mock_contact
    mock_get_contact.assert_called_once_with(mock_db_session, 1)


@pytest.mark.asyncio
@patch('app.crud.get_contacts')
async def test_get_contacts(mock_get_contacts):
    # Мокування
    mock_db_session = AsyncMock()
    mock_contacts = [MagicMock(Contact), MagicMock(Contact)]
    mock_get_contacts.return_value = mock_contacts

    result = await get_contacts(mock_db_session, 0, 10)

    # Перевірка результату
    assert result == mock_contacts
    mock_get_contacts.assert_called_once_with(mock_db_session, 0, 10)


@pytest.mark.asyncio
@patch('app.crud.Contact')
@patch('app.crud.AsyncSession')
async def test_create_contact(mock_AsyncSession, mock_Contact):
    # Мокування
    mock_db_session = AsyncMock()
    mock_Contact.return_value = MagicMock(Contact)
    mock_db_session.add = AsyncMock()
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    contact_data = ContactCreate(name="John Doe", email="john@example.com")
    result = await create_contact(mock_db_session, contact_data)

    # Перевірка результату
    mock_Contact.assert_called_once_with(**contact_data.dict())
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()
    assert result == mock_Contact.return_value


@pytest.mark.asyncio
@patch('app.crud.get_contact')
@patch('app.crud.AsyncSession')
async def test_update_contact(mock_AsyncSession, mock_get_contact):
    # Мокування
    mock_db_session = AsyncMock()
    mock_contact = MagicMock(Contact)
    mock_get_contact.return_value = mock_contact
    contact_update = ContactUpdate(name="Updated Name")

    result = await update_contact(mock_db_session, 1, contact_update)

    # Перевірка результату
    mock_get_contact.assert_called_once_with(mock_db_session, 1)
    mock_contact.__setattr__.assert_called_once_with('name', 'Updated Name')
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()
    assert result == mock_contact


@pytest.mark.asyncio
@patch('app.crud.get_contact')
@patch('app.crud.AsyncSession')
async def test_delete_contact(mock_AsyncSession, mock_get_contact):
    # Мокування
    mock_db_session = AsyncMock()
    mock_contact = MagicMock(Contact)
    mock_get_contact.return_value = mock_contact
    mock_db_session.delete = AsyncMock()
    mock_db_session.commit = AsyncMock()

    result = await delete_contact(mock_db_session, 1)

    # Перевірка результату
    mock_get_contact.assert_called_once_with(mock_db_session, 1)
    mock_db_session.delete.assert_called_once_with(mock_contact)
    mock_db_session.commit.assert_called_once()
    assert result == mock_contact
