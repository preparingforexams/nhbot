import os
import sys

from telegram.ext import CommandHandler, Updater, MessageHandler, Filters

from telegram_bot import Bot, create_logger


def start(bot_token: str, state_file: str):
    logger = create_logger("start")
    logger.debug("Start bot")

    updater = Updater(token=bot_token, use_context=True)
    bot = Bot(updater, state_file)

    dispatcher = updater.dispatcher

    logger.debug("Register command handlers")
    # CommandHandler
    dispatcher.add_handler(CommandHandler("users", bot.show_users))
    dispatcher.add_handler(CommandHandler("nh", bot.nh))

    # chat_admin
    dispatcher.add_handler(CommandHandler("delete_chat", bot.delete_chat))
    dispatcher.add_handler(CommandHandler("get_data", bot.get_data))
    dispatcher.add_handler(CommandHandler("mute", bot.mute, pass_args=True))
    dispatcher.add_handler(CommandHandler("unmute", bot.unmute, pass_args=True))
    dispatcher.add_handler(CommandHandler("kick", bot.kick, pass_args=True))

    # Debugging
    dispatcher.add_handler(CommandHandler("status", bot.status))
    dispatcher.add_handler(CommandHandler("server_time", bot.server_time))
    dispatcher.add_handler(CommandHandler("version", bot.version))

    # MessageHandler
    dispatcher.add_handler(MessageHandler(Filters.command, bot.handle_unknown_command))
    dispatcher.add_handler(
        MessageHandler(Filters.text | Filters.video | Filters.audio | Filters.photo, bot.handle_message))
    dispatcher.add_handler(
        MessageHandler(Filters.status_update.left_chat_member, bot.handle_left_chat_member))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, bot.new_member))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_title, bot.new_chat_title))
    dispatcher.add_handler(MessageHandler(Filters.status_update.chat_created, bot.chat_created))
    dispatcher.add_handler(MessageHandler(Filters.status_update.migrate, bot.migrate_chat_id))

    logger.debug(f"Read state from {state_file}")
    if os.path.exists(state_file):
        with open(state_file) as file:
            try:
                state = json.load(file)
                bot.set_state(state)
            except json.decoder.JSONDecodeError as e:
                logger.warning(f"Unable to load previous state: {e}")

    logger.info("Running")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    import json

    raw_token = os.getenv("BOT_TOKEN")
    token = raw_token.strip() if raw_token else None
    if not token and os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            content = json.load(f)
            token = content.get('token', os.getenv("BOT_TOKEN"))
            if not token:
                raise ValueError("`token` not defined, either set `BOT_TOKEN` or `token` in `secrets.json`")

    if not token:
        raise ValueError("No token has been specified")

    state_filepath = "state.json" if os.path.exists("state.json") else "/data/state.json"
    # noinspection PyBroadException
    try:
        start(token, state_filepath)
    except Exception as e:
        create_logger("__main__").error(e)
        sys.exit(1)
