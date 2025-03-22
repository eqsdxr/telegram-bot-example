from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger
from sys import stderr


logger.add(stderr, format="{time} {level} {message}", level="INFO")


class Settings(BaseSettings):
    BOT_TOKEN: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    ATLAS_URI: str
    DB_NAME: str

    START_MESSAGE: str = (
        "Welcome to rss news reader bot"
        "\nChoose the option:"
        "\n/get {number} - scrap news"
        "\n/add {rss_link} - add rss news source"
    )
    HELP_MESSAGE: str = ""


@lru_cache(maxsize=1)  # Optimize performance by caching
def get_settings():
    return Settings()  # type: ignore # Suppress useless warning


app_settings = get_settings()
