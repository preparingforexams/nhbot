import re
from typing import Tuple, Union, Callable

from bs4 import BeautifulSoup
from telegram import ParseMode, Update, Message
from telegram.ext import CallbackContext, Updater

from .logger import create_logger

NH_TEXT_REGEX = re.compile(r".*\bnh\b.*", re.IGNORECASE | re.MULTILINE)


def is_nh_text(text: str) -> bool:
    return "nh" == text or NH_TEXT_REGEX.match(text)


def is_nh_spoiler(update: Update) -> bool:
    entities = update.effective_message.entities or update.effective_message.caption_entities

    if any(entity.type == "spoiler" for entity in entities):
        html = update.effective_message.text_html or update.effective_message.caption_html
        soup = BeautifulSoup(html, "html.parser")
        spoilers = soup.find_all("span", {"class": "tg-spoiler"})
        for spoiler in spoilers:
            if is_nh_text(" ".join(spoiler.strings)):
                return True

    return False


def convert_number(match: re.Match, update: Update, calc_fn: Callable[[float], float], unit_name: str):
    value = match.group("number")
    if value is None:
        update.effective_message.reply_text("couldn't find a valid number")
        return
    value = value.replace(",", ".")
    try:
        freedom = float(value)
        result = calc_fn(freedom)
        update.effective_message.reply_text(f"{result:.2f}{unit_name}")
    except ValueError:
        update.effective_message.reply_text(f"couldn't parse number (`{value}`) as float")


regex_match_number_with_prefix = r"(?P<number>[-+]?\d+(:?(:?,|\.)\d+)?)"

units: dict[str, dict[str, Union[re.Pattern, Callable[[re.Match, Update], None]]]] = {
    "fahrenheit": {
        "regex": re.compile(rf"{regex_match_number_with_prefix}\s*°?F", re.IGNORECASE),
        "process": lambda m, u: convert_number(m, u, lambda n: (n - 32) * (5 / 9), "°C")
    },
    "inches": {
        "regex": re.compile(rf"{regex_match_number_with_prefix}\s*(:?\"|in(:?ch(:?es)?)?)\b"),
        "process": lambda m, u: convert_number(m, u, lambda n: n * 2.54, "cm")
    },
    "pound": {
        "regex": re.compile(rf"{regex_match_number_with_prefix}\s*(:?pound|lb)(:?s)?\b"),
        "process": lambda m, u: convert_number(m, u, lambda n: n * 453.59237, "gram")
    }
}


def match_unit(unit: dict, args: str) -> re.Match | None:
    regex: re.Pattern = unit["regex"]
    if match := regex.match(args):
        return match

    return None


def find_matching_unit(args: str) -> Tuple[re.Match, dict] | None:
    for unit in units.values():
        if match := match_unit(unit, args):
            return match, unit

    return None


class Bot:
    def __init__(self, updater: Updater):
        self.updater = updater
        self.logger = create_logger("nhbot")

    def send_nh_sticker(self, chat_id: int, message_id: str,
                        sticker_id: str = "CAACAgIAAxkBAAIMHmAPFkBuPZpefXalATwEaInrpyEKAAIPAAPgLXoN0KhdkOTTb1EeBA") -> None:
        self.updater.bot.send_sticker(chat_id=chat_id, sticker=sticker_id, reply_to_message_id=message_id)

    def handle_message(self, update: Update, _: CallbackContext) -> None:
        if update.edited_message:
            return None

        self.logger.info("Handle message: {}".format(update.effective_message.text))
        if update.effective_message:
            message = update.effective_message
            text = message.text if message.text else message.caption
            if is_nh_spoiler(update):
                self.send_message(chat_id=str(update.effective_message.chat_id), text="||nh||",
                                  parse_mode=ParseMode.MARKDOWN_V2)
            elif text and is_nh_text(text):
                self.send_nh_sticker(chat_id=update.effective_message.chat_id,
                                     message_id=update.effective_message.message_id)
        return None

    def nh(self, update: Update, _: CallbackContext) -> None:
        if is_nh_spoiler(update):
            self.send_message(chat_id=str(update.effective_message.chat_id), text="||nh||",
                              parse_mode=ParseMode.MARKDOWN_V2)
        else:
            self.send_nh_sticker(chat_id=update.effective_message.chat_id,
                                 message_id=update.effective_message.message_id)

    def send_message(self, *, chat_id: str, text: str, **kwargs) -> Message:
        return self.updater.bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True, **kwargs)

    @staticmethod
    def cure(update: Update, _: CallbackContext):
        args = update.effective_message.text.split(" ", maxsplit=1)[1]
        unit = find_matching_unit(args)
        if unit is None:
            update.effective_message.reply_text("couldn't find a valid unit to convert")
        else:
            match, unit = unit
            unit["process"](match, update)
