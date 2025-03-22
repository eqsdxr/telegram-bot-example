import pytest
import feedparser
from unittest.mock import AsyncMock, patch
from telegram import CallbackQuery, Chat, InlineKeyboardMarkup, User
from telegram.ext import ContextTypes

from app.bot.config import app_settings
from app.bot import main
from app.bot import exc


@pytest.mark.asyncio
async def test_start():
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


@pytest.mark.asyncio
async def test_get_help():
    user = User(id=12345, first_name="TestUser", is_bot=False)
    chat = Chat(id=67890, type="private")

    update = AsyncMock()
    update.effective_user = user
    update.effective_chat = chat

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.send_message = AsyncMock()

    await main.get_help(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890, text=app_settings.HELP_MESSAGE
    )


@pytest.mark.asyncio
async def test_unknown():
    user = User(id=12345, first_name="TestUser", is_bot=False)
    chat = Chat(id=67890, type="private")

    update = AsyncMock()
    update.effective_user = user
    update.effective_chat = chat

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.send_message = AsyncMock()

    await main.unknown(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890, text=app_settings.UNKNOWN_MESSAGE
    )


@pytest.mark.asyncio
async def test_get_news_invalid_number():
    update = AsyncMock()
    update.effective_user = User(id=12345, first_name="TestUser", is_bot=False)
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["invalid_number"]  # Non-integer input
    context.bot.send_message = AsyncMock()

    await main.get_news(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890, text="Provide a valid number."
    )


@pytest.mark.asyncio
async def test_get_news_no_rss_feeds():
    update = AsyncMock()
    update.effective_user = User(id=12345, first_name="TestUser", is_bot=False)
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["5"]
    context.bot.send_message = AsyncMock()

    with patch("app.bot.main.get_db_user", return_value=None):
        await main.get_news(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890, text="You have no RSS feeds added."
    )


@pytest.mark.asyncio
async def test_get_news_success():
    """Test successful news retrieval."""
    update = AsyncMock()
    update.effective_user = User(id=12345, first_name="TestUser", is_bot=False)
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["2"]  # User requests 2 news items
    context.bot.send_message = AsyncMock()

    mock_user_data = {"rss_list": [{"url": "https://rss.com/feed"}]}

    mock_feed = feedparser.FeedParserDict(
        {
            "feed": feedparser.FeedParserDict({"title": "Test RSS Feed"}),
            "entries": [
                feedparser.FeedParserDict(
                    {"title": "News 1", "link": "https://news1.com"}
                ),
                feedparser.FeedParserDict(
                    {"title": "News 2", "link": "https://news2.com"}
                ),
                feedparser.FeedParserDict(
                    {"title": "News 3", "link": "https://news3.com"}
                ),
            ],
        }
    )

    with (
        patch("app.bot.main.get_db_user", return_value=mock_user_data),
        patch("app.bot.main.get_rss_data", return_value=mock_feed),
    ):
        await main.get_news(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890,
        text="\n\nNews 1\nhttps://news1.com\n\nNews 2\nhttps://news2.com",
    )


@pytest.mark.asyncio
async def test_get_news_long_messages():
    """Test message splitting when text exceeds Telegram's limit."""
    update = AsyncMock()
    update.effective_user = User(id=12345, first_name="TestUser", is_bot=False)
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["3"]
    context.bot.send_message = AsyncMock()

    mock_user_data = {"rss_list": [{"url": "https://rss.com/feed"}]}

    link = "https://longnews.com"
    long_text = "A" * 3900  # Simulate a long entry

    mock_feed = feedparser.FeedParserDict(
        {
            "feed": feedparser.FeedParserDict({"title": "Test RSS Feed"}),
            "entries": [
                feedparser.FeedParserDict({"title": long_text, "link": link})
            ]
            * 3,
        }
    )

    with (
        patch("app.bot.main.get_db_user", return_value=mock_user_data),
        patch("app.bot.main.get_rss_data", return_value=mock_feed),
    ):
        await main.get_news(update, context)

    assert (
        context.bot.send_message.call_count == 3
    )  # Three split messages sent


def test_get_rss_data_valid():
    mock_feed = feedparser.FeedParserDict(
        {
            "bozo": 0,
            "feed": {"title": "Valid Feed"},
            "entries": [{"title": "News 1", "link": "https://news1.com"}],
        }
    )

    with patch("app.bot.main.get_rss_data", return_value=mock_feed):
        result = main.get_rss_data("https://valid-rss.com/feed")

    assert result.feed["title"] == "Valid Feed"
    assert len(result.entries) == 1
    assert result.entries[0]["title"] == "News 1"


def test_get_rss_data_invalid():
    mock_feed = feedparser.FeedParserDict(
        {"bozo": 1}
    )  # Simulating an invalid feed

    with (
        patch("feedparser.parse", return_value=mock_feed),
        pytest.raises(exc.InvalidRSSURLError),
    ):
        main.get_rss_data("https://invalid-rss.com/feed")


@pytest.mark.asyncio
async def test_add_feed_success():
    update = AsyncMock()
    update.effective_user = User(id=12345, first_name="TestUser", is_bot=False)
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["https://valid-rss.com/feed"]
    context.bot.send_message = AsyncMock()

    with (
        patch("app.bot.main.get_rss_data") as mock_get_rss,
        patch("app.bot.main.add_rss_to_user") as mock_add_rss,
    ):
        mock_get_rss.return_value.feed.title = "Tech News"

        await main.add_feed(update, context)

        mock_get_rss.assert_called_once_with("https://valid-rss.com/feed")
        mock_add_rss.assert_called_once_with(
            update.effective_user, "https://valid-rss.com/feed", "Tech News"
        )
        context.bot.send_message.assert_called_once_with(
            chat_id=67890,
            text="RSS feed successfully added. Now you can access the latest news.",
        )


@pytest.mark.asyncio
async def test_add_feed_no_url():
    update = AsyncMock()
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    context.bot.send_message = AsyncMock()

    await main.add_feed(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890, text="Provide RSS url."
    )


@pytest.mark.asyncio
async def test_add_feed_invalid_url():
    update = AsyncMock()
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["https://invalid-rss.com/feed"]
    context.bot.send_message = AsyncMock()

    with patch(
        "app.bot.main.get_rss_data", side_effect=exc.InvalidRSSURLError
    ):
        await main.add_feed(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890, text="RSS url is invalid or broken."
    )


@pytest.mark.asyncio
async def test_add_feed_already_exists():
    update = AsyncMock()
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["https://duplicate-rss.com/feed"]
    context.bot.send_message = AsyncMock()

    with (
        patch("app.bot.main.get_rss_data") as mock_get_rss,
        patch("app.bot.main.add_rss_to_user", side_effect=exc.RSSAlreadyExist),
    ):
        mock_get_rss.return_value.feed.title = "Duplicate News"

        await main.add_feed(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890, text="You have already subscribed to this RSS."
    )


@pytest.mark.asyncio
async def test_remove_feed_no_rss():
    update = AsyncMock()
    update.effective_user = User(id=12345, first_name="TestUser", is_bot=False)
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.send_message = AsyncMock()

    with patch("app.bot.main.get_db_user", return_value=None):
        await main.remove_feed(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890,
        text="You have no RSS feeds added.",
    )


@pytest.mark.asyncio
async def test_remove_feed_shows_rss_list():
    update = AsyncMock()
    update.effective_user = User(id=12345, first_name="TestUser", is_bot=False)
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.send_message = AsyncMock()

    mock_user_data = {"rss_list": [{"title": "Feed1"}, {"title": "Feed2"}]}

    with patch("app.bot.main.get_db_user", return_value=mock_user_data):
        await main.remove_feed(update, context)

    context.bot.send_message.assert_called_once()
    _, kwargs = context.bot.send_message.call_args
    assert kwargs["text"] == "Choose which one to delete."
    assert isinstance(kwargs["reply_markup"], InlineKeyboardMarkup)
    assert len(kwargs["reply_markup"].inline_keyboard) == 2


@pytest.mark.asyncio
async def test_remove_button_handler_success():
    update = AsyncMock()
    update.effective_user = User(id=12345, first_name="TestUser", is_bot=False)

    query = AsyncMock(spec=CallbackQuery)
    query.data = "Feed1"
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()

    update.callback_query = query
    context = AsyncMock()

    with patch("app.bot.main.remove_rss") as mock_remove_rss:
        await main.remove_button_handler(update, context)

    query.answer.assert_called_once()
    mock_remove_rss.assert_called_once_with(update.effective_user, "Feed1")
    query.edit_message_text.assert_called_once_with(
        text="Successfully removed."
    )


@pytest.mark.asyncio
async def test_remove_button_handler_value_error():
    update = AsyncMock()
    query = AsyncMock(spec=CallbackQuery)
    query.data = "Feed1"
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()

    update.callback_query = query
    context = AsyncMock()

    with patch("app.bot.main.remove_rss", side_effect=ValueError):
        await main.remove_button_handler(update, context)

    query.answer.assert_called_once()
    query.edit_message_text.assert_called_once_with(
        text="Error. Nothing was removed."
    )


@pytest.mark.asyncio
async def test_remove_button_handler_unexpected_deletion():
    """Test handling of UnexpectedDeletionError."""
    update = AsyncMock()
    query = AsyncMock(spec=CallbackQuery)
    query.data = "Feed1"
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()

    update.callback_query = query
    context = AsyncMock()

    with patch(
        "app.bot.main.remove_rss", side_effect=exc.UnexpectedDeletionError
    ):
        await main.remove_button_handler(update, context)

    query.answer.assert_called_once()
    query.edit_message_text.assert_called_once_with(
        text="Error. Deleted more than one value."
    )


@pytest.mark.asyncio
async def test_get_status_no_feeds():
    update = AsyncMock()
    update.effective_user = User(id=12345, first_name="TestUser", is_bot=False)
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.send_message = AsyncMock()

    with patch("app.bot.main.get_db_user", return_value={"rss_list": []}):
        await main.get_status(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=67890, text="You have no RSS feeds added."
    )


@pytest.mark.asyncio
async def test_get_status_few_feeds():
    """Test when the user has a small number of RSS feeds."""
    update = AsyncMock()
    update.effective_user = User(id=12345, first_name="TestUser", is_bot=False)
    update.effective_chat = Chat(id=67890, type="private")

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.send_message = AsyncMock()

    mock_user_data = {
        "rss_list": [
            {"title": "Feed 1"},
            {"title": "Feed 2"},
        ]
    }

    with patch("app.bot.main.get_db_user", return_value=mock_user_data):
        await main.get_status(update, context)

    assert context.bot.send_message.call_count == 2
    context.bot.send_message.assert_any_call(
        chat_id=67890, text="You have 2 RSS feeds added."
    )
    context.bot.send_message.assert_any_call(
        chat_id=67890, text="\n1. Feed 1\n2. Feed 2"
    )
