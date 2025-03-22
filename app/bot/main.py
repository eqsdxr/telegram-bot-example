from typing import cast

from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    User,
)

from app.bot.config import app_settings, logger
from app.bot.db import add_rss_to_user, get_db_user, remove_rss
from app.bot.exc import (
    InvalidRSSURLError,
    RSSAlreadyExist,
    UnexpectedDeletionError,
)
from app.bot.feed import get_rss_data


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(
        "User %s started the conversation.",
        cast(User, update.effective_user).first_name,
    )
    await context.bot.send_message(
        chat_id=cast(Chat, update.effective_chat).id,
        text=app_settings.START_MESSAGE,
    )


async def get_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=cast(Chat, update.effective_chat).id,
        text=app_settings.HELP_MESSAGE,
    )


async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(
            cast(list[str], context.args)[0]
        )  # Get user-specified news count
    except (IndexError, ValueError):
        await context.bot.send_message(
            chat_id=cast(Chat, update.effective_chat).id,
            text="Provide a valid number.",
        )
        return

    user_data = get_db_user(cast(User, update.effective_user))

    if (
        not user_data
        or "rss_list" not in user_data
        or not user_data["rss_list"]
    ):
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
        add_rss_to_user(
            cast(User, update.effective_user), rss_url, feed.feed.title
        )
        message = (
            "RSS feed successfully added. Now you can access the latest news."
        )
    except IndexError:
        message = "Provide RSS url."
    except InvalidRSSURLError:
        message = "RSS url is invalid or broken."
    except RSSAlreadyExist:
        message = "You have already subscribed to this RSS."

    await context.bot.send_message(
        chat_id=cast(Chat, update.effective_chat).id, text=message
    )


async def remove_feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = get_db_user(cast(User, update.effective_user))

    if (
        not user_data
        or "rss_list" not in user_data
        or not user_data["rss_list"]
    ):
        await context.bot.send_message(
            chat_id=cast(Chat, update.effective_chat).id,
            text="You have no RSS feeds added.",
        )
        return

    keyboard = []
    for rss in user_data["rss_list"]:
        keyboard.append(
            [InlineKeyboardButton(rss["title"], callback_data=rss["title"])]
        )
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=cast(Chat, update.effective_chat).id,
        reply_markup=reply_markup,
        text="Choose which one to delete.",
    )


async def remove_button_handler(
    update: Update, context: CallbackContext
) -> None:
    query = update.callback_query
    await cast(CallbackQuery, query).answer()
    button_value = cast(CallbackQuery, query).data
    try:
        remove_rss(cast(User, update.effective_user), cast(str, button_value))
        message = "Successfully removed."
    except ValueError:
        message = "Error. Nothing was removed."
    except UnexpectedDeletionError:
        message = "Error. Deleted more than one value."
    await cast(CallbackQuery, query).edit_message_text(text=message)


async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = get_db_user(cast(User, update.effective_user))

    if (
        not user_data
        or "rss_list" not in user_data
        or not user_data["rss_list"]
    ):
        await context.bot.send_message(
            chat_id=cast(Chat, update.effective_chat).id,
            text="You have no RSS feeds added.",
        )
        return

    messages = ["You have {} rss added.".format(len(user_data["rss_list"]))]
    message = ""

    for count, rss in enumerate(user_data["rss_list"]):
        status = "\n{}. {}".format(
            count + 1, rss["title"]
        )  # Show count starting from 1

        if len(message) + len(status) > 4000:
            messages.append(message)

        message += status

    if message:
        messages.append(message)

    for msg in messages:
        await context.bot.send_message(
            chat_id=cast(Chat, update.effective_chat).id, text=msg
        )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=cast(Chat, update.effective_chat).id, text="Unknown command."
    )


if __name__ == "__main__":
    app = ApplicationBuilder().token(app_settings.BOT_TOKEN).build()
    start_handler = CommandHandler("start", start)
    get_help_handler = CommandHandler("help", get_help)
    get_news_handler = CommandHandler("get", get_news)
    add_feed_handler = CommandHandler("add", add_feed)
    remove_feed_handler = CommandHandler("remove", remove_feed)
    get_status_handler = CommandHandler("status", get_status)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    app.add_handler(start_handler)
    app.add_handler(get_help_handler)
    app.add_handler(get_news_handler)
    app.add_handler(add_feed_handler)
    app.add_handler(remove_feed_handler)
    app.add_handler(CallbackQueryHandler(remove_button_handler))
    app.add_handler(get_status_handler)
    app.add_handler(unknown_handler)
    app.run_polling()
