from typing import cast

from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram import Chat, Update, User

from app.bot.config import app_settings
from app.bot.db import add_rss_to_user, get_db_user
from app.bot.exc import InvalidRSSURLError, RSSAlreadyExist
from app.bot.feed import get_rss_data


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=cast(Chat, update.effective_chat).id,
        text=(
            "Welcome to rss news reader bot"
            "\nChoose the option:"
            "\n/get {number} - scrap news"
            "\n/add {rss_link} - add rss news source"
        ),
    )


async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(cast(list[str], context.args)[0])  # Get user-specified news count
    except (IndexError, ValueError):
        await context.bot.send_message(
            chat_id=cast(Chat, update.effective_chat).id, text="Provide a valid number."
        )
        return

    user_data = get_db_user(cast(User, update.effective_user))

    if not user_data or "rss_list" not in user_data or not user_data["rss_list"]:
        await context.bot.send_message(
            chat_id=cast(Chat, update.effective_chat).id,
            text="You have no RSS feeds added.",
        )
        return

    messages = []
    message = ""

    for rss in user_data["rss_list"]:
        feed = get_rss_data(rss["url"])

        for entry in feed.entries[:amount]:
            entry_text = f"\n\n{entry.title}\n{entry.link}"

            # Split message if it's too long
            if len(message) + len(entry_text) > 4000:
                messages.append(message)
                message = ""

            message += entry_text

    if message:
        messages.append(message)

    for msg in messages:
        await context.bot.send_message(
            chat_id=cast(Chat, update.effective_chat).id, text=msg
        )


async def add_feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rss_url: str = cast(list[str], context.args)[0]
        feed = get_rss_data(rss_url)
        add_rss_to_user(cast(User, update.effective_user), rss_url, feed.feed.title)
    except IndexError:
        await context.bot.send_message(
            chat_id=cast(Chat, update.effective_chat).id,
            text="Provide RSS url.",
        )
        return
    except InvalidRSSURLError:
        await context.bot.send_message(
            chat_id=cast(Chat, update.effective_chat).id,
            text="RSS url is invalid or broken.",
        )
        return
    except RSSAlreadyExist:
        await context.bot.send_message(
            chat_id=cast(Chat, update.effective_chat).id,
            text="You have already subscribed to this RSS.",
        )
        return

    await context.bot.send_message(
        chat_id=cast(Chat, update.effective_chat).id,
        text="RSS feed successfully added. Now you can access the latest news.",
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=cast(Chat, update.effective_chat).id, text="Unknown command."
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(app_settings.BOT_TOKEN).build()
    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", start)
    get_news_handler = CommandHandler("get", get_news)
    add_feed_handler = CommandHandler("add", add_feed)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(start_handler)
    application.add_handler(get_news_handler)
    application.add_handler(add_feed_handler)
    application.add_handler(unknown_handler)
    application.run_polling()
