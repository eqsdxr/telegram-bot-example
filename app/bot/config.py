from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger
from sys import stderr


logger.add(stderr, format="{time} {level} {message}", level="INFO")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    BOT_TOKEN: str

    ATLAS_URI: str  # MongoDB connection string
    DB_NAME: str

    START_MESSAGE: str = (
        "Welcome to rss news reader bot"
        "\nChoose an option:"
        "\n/get <number> - scrap <number> news"
        "\n/add <rss_link> - add rss news source"
        "\n/remove - remove feed"
        "\n/status - get status"
        "\n/help - get help"
    )

    HELP_MESSAGE: str = (
        "\n/get <number> - scrap <number> news"
        "\n/add <rss_link> - add rss news source"
        "\n/remove - remove feed"
        "\n/status - get status"
        "\n/help - get help"
    )

    UNKNOWN_MESSAGE: str = "Unknown command."


@lru_cache(maxsize=1)  # Optimize performance by caching
def get_settings():
    return Settings()  # type: ignore # Suppress useless warning


app_settings = get_settings()
