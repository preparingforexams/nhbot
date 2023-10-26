import os
import sys

from telegram.ext import CommandHandler, Updater, MessageHandler, Filters

from telegram_bot import Bot, create_logger


def start(bot_token: str):
    logger = create_logger("start")
    logger.debug("Start bot")

    updater = Updater(token=bot_token, use_context=True)
    bot = Bot(updater)

    dispatcher = updater.dispatcher

    logger.debug("Register command handlers")
    # CommandHandler
    dispatcher.add_handler(CommandHandler("nh", bot.nh))
    dispatcher.add_handler(CommandHandler("cure_freedom", bot.cure))
    dispatcher.add_handler(CommandHandler("cf", bot.cure))
    dispatcher.add_handler(CommandHandler("supported_units", bot.supported_units))
    dispatcher.add_handler(
        MessageHandler(Filters.text | Filters.video | Filters.audio | Filters.photo, bot.handle_message))

    logger.info("Running")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    raw_token = os.getenv("BOT_TOKEN")
    token = raw_token.strip() if raw_token else None
    if not token:
        raise ValueError("No token has been specified")

    # noinspection PyBroadException
    try:
        start(token)
    except Exception as e:
        create_logger("__main__").error(e)
        sys.exit(1)
