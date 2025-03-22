import pytest
from unittest.mock import AsyncMock
from telegram import Chat, User
from telegram.ext import ContextTypes

from app.bot.config import app_settings
from app.bot import main


@pytest.mark.asyncio
async def test_start_command():
    user = User(id=12345, first_name="TestUser", is_bot=False)
    chat = Chat(id=67890, type="private")

    update = AsyncMock()
    update.effective_user = user
    update.effective_chat = chat

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.send_message = AsyncMock()

    await main.start(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890, text=app_settings.START_MESSAGE
    )
