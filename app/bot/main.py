import asyncio
import telegram

from app.bot.config import app_settings


async def main():
    bot = telegram.Bot(app_settings.BOT_TOKEN)
    async with bot:
        print(await bot.get_me())


if __name__ == "__main__":
    asyncio.run(main())
