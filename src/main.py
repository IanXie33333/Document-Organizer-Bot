from bot.client import DriveBot
from config.logging import configure_logging
from config.settings import get_settings
from db.base import Base
import db.models  # noqa: F401
from db.session import engine


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    Base.metadata.create_all(bind=engine)

    bot = DriveBot()
    bot.run(settings.discord_bot_token)


if __name__ == '__main__':
    main()
