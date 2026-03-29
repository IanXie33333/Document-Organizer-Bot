from bot.client import DriveBot
from config.logging import configure_logging
from config.settings import get_settings


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    bot = DriveBot()
    bot.run(settings.discord_bot_token)


if __name__ == '__main__':
    main()
