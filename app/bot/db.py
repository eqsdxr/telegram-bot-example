from loguru import logger
from pymongo import MongoClient
from telegram import User

from app.bot.config import app_settings
from app.bot.exc import RSSAlreadyExist

client = MongoClient(app_settings.ATLAS_URI)
db = client["app"]
users_collection = db["users"]


def add_user(user: User):
    users_collection.update_one(
        {"user_id": user.id},
        {"$set": {"rss_list": []}},
        upsert=True,  # Create if doesn't exist
    )


def get_db_user(user: User):
    db_user = users_collection.find_one({"user_id": user.id})
    if not db_user:
        add_user(user)
        db_user = users_collection.find_one({"user_id": user.id})
        if not db_user:
            err_msg = "Database error: Failed to retrieve user after insertion"
            logger.error(err_msg)
            raise RuntimeError(err_msg)
    return db_user


def delete_user(user_id):
    users_collection.delete_one({"user_id": user_id})


def add_rss_to_user(user: User, rss_url: str, rss_title: str):
    db_user = get_db_user(user)
    if rss_url in [entity["url"] for entity in db_user["rss_list"]]:
        raise RSSAlreadyExist()
    users_collection.update_one(
        {"user_id": user.id},
        {"$addToSet": {"rss_list": {"url": rss_url, "title": rss_title}}},
        upsert=True,
    )
