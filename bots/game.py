import slack
from slack.errors import SlackApiError
import re
import logging
from libs.manager import gameManager
from slackapi.client import send_msg, send_private_msg_in_channel, update_msg, delete_msg, get_username
from slackapi.payload import card_to_emoji
from typing import Dict


logger = logging.getLogger(__name__)
HELP_MSG = """Try commands below:
`help` to print this msg,
`open <name>(optional)` to create a table as <name>,
`join <name>(optional)` to sit at a table as <name>,
`reopen <name>(optional)` to reopen a table as <name>,
`start` to start a game or continue next game,
`continue` to continue next game,
`leave` or `quit` to leave table,
`bot` to ask a bot to join in,
`chip` to check current chips you have.
support the following poker operations:
`bet <number>` for raise <number>,
`call`, `all`, `check`, `fold`.
"""


class ChannelInfo:
    def __init__(self, table_id: str, client: slack.WebClient):
        self.table_id = table_id
        self.client = client


def handle_message(web_client: slack.WebClient, channel: str, user: str, ts: str, text: str, mentioned: bool):
    def _get_username(s: str) -> str:
        if len(s.split()) >= 2:
            return " ".join(s.split()[1:])
        else:
            return get_username(web_client, user)

    if re.search(r"^open((\s)+(\w)*)*$", text) is not None:
        create_table(web_client, channel, user, _get_username(text))
    elif re.search(r"^join((\s)+(\w)*)*$", text) is not None:
        join_table(web_client, channel, user, _get_username(text))
    elif re.search(r"^reopen((\s)+(\w)*)*$", text) is not None:
        reopen_table(web_client, channel, user, _get_username(text))
    elif text == "start":
        start_game(web_client, channel, user)
    elif re.search(r"^bet(\s)+(\d)+$", text) is not None:
        chip = int(text.split()[1])
        bet(web_client, channel, user, chip)
    elif text == "call":
        call(web_client, channel, user)
    elif text == "all":
        all_in(web_client, channel, user)
    elif text == "check":
        check(web_client, channel, user)
    elif text == "fold":
        fold(web_client, channel, user)
    elif text == "continue":
        start_game(web_client, channel, user)
    elif text == "leave" or text == "quit":
        leave_table(web_client, channel, user)
    elif text == "info":
        echo_info(web_client, channel)
    elif text == "bot":
        add_bot(web_client, channel)
    elif text == "make me rich":
        gain_chip(web_client, channel, user)
    elif text == "chip":
        show_chip(web_client, channel, user)
    else:
        if mentioned or text == "help":
            send_msg(web_client, channel, HELP_MSG, user)


channels: Dict[str, ChannelInfo] = dict()


def create_table(web_client: slack.WebClient, channel: str, user: str, username: str):
    if channel in channels.keys():
        send_msg(web_client, channel,
                 "Failed to open a game, because there is an unfinished game in this channel! "
                 "If you want to reopen the table, type `reopen` instead")
        return

    table_id = gameManager.open(user)
    channels[channel] = ChannelInfo(table_id, web_client)
    send_msg(web_client, channel,
             "Successfully opened a game! Everyone is free to join the table.")
    join_table(web_client, channel, user, username)


def reopen_table(web_client: slack.WebClient, channel: str, user: str, username: str):
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


def join_table(web_client: slack.WebClient, channel: str, user: str, username: str):
    # TODO: use wrapper to check channel
    if channel not in channels.keys():
        send_msg(web_client, channel,
                 "Failed to join the table, because there is no opened game in this channel.")
        return
    table_id = channels[channel].table_id

    pos, total_chip, table_chip, err = gameManager.join(table_id, user, username)
    if err is not None:
        send_msg(web_client, channel, err)
        return

    send_msg(web_client, channel,
             f"just joined at position {pos}, total player: {pos + 1}", user)

    if pos + 1 == 2:
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
    nplayer, err = gameManager.leave(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)
        return

    send_msg(web_client, channel, f"just leaf the table, total player: {nplayer}", user)


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


def add_bot(web_client: slack.WebClient, channel: str):
    if channel not in channels.keys():
        send_msg(web_client, channel,
                 "Failed to continue, because there is no opened game in this channel.")
        return
    table_id = channels[channel].table_id
    err = gameManager.add_bot(table_id)
    if err is not None:
        send_msg(web_client, channel, err)
        return


def bet(web_client: slack.WebClient, channel: str, user: str, chip):
    table_id = channels[channel].table_id
    err = gameManager.bet(table_id, user, int(chip))
    if err is not None:
        send_msg(web_client, channel, err)


def call(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.call(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)


def all_in(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.all_in(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)


def check(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.check(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)


def fold(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.fold(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)


def echo_info(web_client: slack.WebClient, channel: str):
    table_id = channels[channel].table_id
    send_msg(web_client, channel, gameManager.get_game_info(table_id))


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
