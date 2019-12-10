import slack
from slack.errors import SlackApiError
import re
import logging
from libs.manager import gameManager
from slackapi.client import send_msg, send_private_msg_in_channel, update_msg, delete_msg, get_username
from slackapi.payload import card_to_emoji
from typing import Dict, Callable


logger = logging.getLogger(__name__)
HELP_MSG = ""


class ChannelInfo:
    def __init__(self, table_id: str, client: slack.WebClient):
        self.table_id = table_id
        self.client = client


class Command:
    def __init__(self, pattern: str, func: Callable, name: str,
                 description: str, need_text: bool = False, debug: bool = False):
        self.pattern = pattern
        self.func = func
        self.name = name
        self.description = description
        self.need_text = need_text
        self.debug = debug

    def call(self, **args):
        if not self.need_text:
            args.pop("text")
        self.func(**args)


def handle_message(web_client: slack.WebClient, channel: str, user: str, ts: str, text: str, mentioned: bool):
    text = text.strip()
    for command in commands:
        if re.search(command.pattern, text, re.IGNORECASE) is not None:
            command.call(web_client=web_client, channel=channel, user=user, text=text)
            return
    if mentioned:
        echo_help(web_client, channel, user)


def _get_username(s: str, web_client: slack.WebClient, userid: str) -> str:
    if len(s.split()) >= 2:
        return " ".join(s.split()[1:])
    else:
        return get_username(web_client, userid)


def create_table(web_client: slack.WebClient, channel: str, user: str, text: str):
    if channel in channels.keys():
        send_msg(web_client, channel,
                 "Failed to open a game, because there is an unfinished game in this channel! "
                 "If you want to reopen the table, type `reopen` instead")
        return

    username = _get_username(text, web_client, user)
    table_id = gameManager.open(user)
    channels[channel] = ChannelInfo(table_id, web_client)
    send_msg(web_client, channel,
             "Successfully opened a game! Everyone is free to join the table.")
    join_table(web_client, channel, user, username)


def reopen_table(web_client: slack.WebClient, channel: str, user: str, text: str):
    username = _get_username(text, web_client, user)
    if channel not in channels.keys():
        send_msg(web_client, channel,
                 "Warning: There is no opened table in this channel. Create table instead.")
        create_table(web_client, channel, user, username)
        return

    gameManager.close(channels[channel].table_id)
    channels.pop(channel)
    send_msg(web_client, channel,
             "Successfully closed table. Reopening...")
    create_table(web_client, channel, user, username)


def join_table(web_client: slack.WebClient, channel: str, user: str, text: str):
    username = _get_username(text, web_client, user)
    if channel not in channels.keys():
        send_msg(web_client, channel,
                 "Failed to join the table, because there is no opened game in this channel.")
        return
    table_id = channels[channel].table_id

    pos, nplayers, total_chip, table_chip, err = gameManager.join(table_id, user, username)
    if err is not None:
        send_msg(web_client, channel, err)
        return

    send_msg(web_client, channel,
             f"{username} just joined at position {pos}, total player: {nplayers}")

    if nplayers == 2:
        send_msg(web_client, channel,
                 'Now you can start a game by replying "start" or wait for more player to join in.')

    send_private_msg_in_channel(
        web_client, channel, user, f"you have ${total_chip}, and spend ${table_chip} to join the table")


def leave_table(web_client: slack.WebClient, channel: str, user: str):
    if channel not in channels.keys():
        send_msg(web_client, channel,
                 "Failed to join the table, because there is no opened game in this channel.")
        return
    table_id = channels[channel].table_id
    nplayers, err = gameManager.leave(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)
        return

    send_msg(web_client, channel, f"just leaf the table, total player: {nplayers}", user)


def start_game(web_client: slack.WebClient, channel: str, user: str):
    if channel not in channels.keys():
        send_msg(web_client, channel,
                 "Failed to start, because there is no opened game in this channel.")
        return
    table_id = channels[channel].table_id

    hands, err = gameManager.start(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)
        return
    for hand in hands:
        card_str = ""
        for card in hand['hand']:
            card_str += card_to_emoji(str(card)) + "  "
        if not hand['id'].startswith("bot"):
            send_private_msg_in_channel(
                web_client, channel, hand["id"], f"Your hand is {card_str}")
        else:
            send_msg(web_client, channel, f"{hand['id']} has {card_str}")
    send_msg(web_client, channel,
             "Game started! I have send your hand to you personally. And type help or @me to get help message")


def add_bot(web_client: slack.WebClient, channel: str, user: str):
    if channel not in channels.keys():
        send_msg(web_client, channel,
                 "Failed to continue, because there is no opened game in this channel.")
        return
    table_id = channels[channel].table_id
    err = gameManager.add_bot(table_id)
    if err is not None:
        send_msg(web_client, channel, err)
        return


def bet(web_client: slack.WebClient, channel: str, user: str, text: str):
    chip = int(text.split()[-1])
    table_id = channels[channel].table_id
    err = gameManager.bet(table_id, user, chip)
    if err is not None:
        send_msg(web_client, channel, err)


def call_or_check(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.call_or_check(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)


def all_in(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.all_in(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)


def fold(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.fold(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)


def echo_info(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    send_msg(web_client, channel, gameManager.get_game_info(table_id))


def gain_chip(web_client: slack.WebClient, channel: str, user: str):
    err = gameManager.gain_chip(user)
    if err is None:
        send_msg(web_client, channel, ", you get $500!", user)
    else:
        send_msg(web_client, channel, err, user)


def show_chip(web_client: slack.WebClient, channel: str, user: str):
    chip, err = gameManager.show_chip(user)
    if err is None:
        send_msg(web_client, channel, f", you have ${chip}", user)
    else:
        send_msg(web_client, channel, err, user)


def echo_help(web_client: slack.WebClient, channel: str, user: str):
    global HELP_MSG
    if HELP_MSG == "":
        for command in commands:
            if not command.debug:
                HELP_MSG += f"`{command.name}`: {command.description}\n"
    send_msg(web_client, channel, HELP_MSG)


def send_to_channel_by_table_id(table_id, msg="void", blocks=None):
    for (channel, info) in channels.items():
        if info.table_id == table_id:
            ts = send_msg(info.client, channel, msg, blocks=blocks)
            return ts, None
    return None, "table_id not found"


def send_private_msg_to_channel_by_table_id(table_id, user, msg="void", blocks=None):
    for (channel, info) in channels.items():
        if info.table_id == table_id:
            if not user.startswith("bot"):
                send_private_msg_in_channel(info.client, channel, user, msg, blocks=blocks)
            return None
    return "table_id not found"


def update_msg_by_table_id(table_id, ts, msg="void", blocks=None):
    for (channel, info) in channels.items():
        if info.table_id == table_id:
            try:
                update_msg(info.client, channel, msg, ts, blocks=blocks)
                return None
            except SlackApiError:
                logger.debug("update msg failed with ts %s, table_id %s", ts, table_id)
                return "send failed"
    return "table_id not found"


def delete_msg_by_table_id(table_id, ts):
    for (channel, info) in channels.items():
        if info.table_id == table_id:
            try:
                delete_msg(info.client, channel, ts)
                return None
            except SlackApiError:
                logger.debug("delete msg failed with ts %s, table_id %s", ts, table_id)
                return "delete failed"
    return "table_id not found"


channels: Dict[str, ChannelInfo] = dict()

commands = (
    Command(r"^open((\s)+(\w)*)*$", create_table, "open <name>", "open a table", need_text=True),
    Command(r"^join((\s)+(\w)*)*$", join_table, "join <name>", "join a table", need_text=True),
    Command(r"^reopen((\s)+(\w)*)*$", reopen_table, "reopen <name>", "reopen a table", need_text=True),
    Command(r"^leave$", leave_table, "leave", "leave the table"),
    Command(r"^start$", start_game, "start", "start a game or continue the game"),
    Command(r"^(b(et)?(\s)+)?(\d)+$", bet, "<bet> num", "bet chips", need_text=True),
    Command(r"^c(all)?$", call_or_check, "c<all>", "call"),
    Command(r"^c(heck)?$", call_or_check, "c<heck>", "check"),
    Command(r"^a(ll)?$", all_in, "a<ll>", "all in"),
    Command(r"^f(old)?$", fold, "f<old>", "fold"),
    Command(r"^bot$", add_bot, "bot", "add a bot to the table"),
    Command(r"^chip$", show_chip, "chip", "show how many chips you have"),
    Command(r"^help$", echo_help, "help", "get help message"),
    Command(r"^info$", echo_info, "info", "show internal state of the current game", debug=True),
    Command(r"^make me rich$", gain_chip, "make me rich", "gain more chips", debug=True)
)
