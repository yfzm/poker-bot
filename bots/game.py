import slack
from slackbot.bot import respond_to
from slackbot.bot import listen_to
import re
from libs.manager import gameManager
from .message_helper import *
import threading
from slackapi.client import *
from typing import Dict


HELP_MSG = """Try commands below:
open to create a table,
join to sit at a table,
start to start a game,
r  for raise,
c  for check,
f  for fold.
a  for all in
ca for call
b  for bet
"""
# CHANNEL_ID = 'CP3P9CS2W'

class ChannelInfo:
    def __init__(self, table_id: str, client: slack.WebClient):
        self.table_id = table_id
        self.client = client


def handle_message(web_client: slack.WebClient, channel: str, user: str, ts: str, text: str, mentioned: bool):
    if text == "open":
        create_table(web_client, channel, user)
    elif text == "join":
        join_table(web_client, channel, user)
    elif text == "start":
        start_game(web_client, channel, user)
    elif text.startswith("bet"):
        bet(web_client, channel, user, 20)
    elif text == "call":
        call(web_client, channel, user)
    elif text == "all":
        all_in(web_client, channel, user)
    elif text == "check":
        check(web_client, channel, user)
    elif text == "fold":
        fold(web_client, channel, user)
    elif text == "continue":
        continue_game(web_client, channel, user)
    elif text == "info":
        echo_info(web_client, channel)
    elif text == "bot":
        add_bot(web_client, channel)
    else:
        if mentioned:
            send_msg(web_client, channel, HELP_MSG, user)


# TODO: 教slackbot说中文
# CHANNEL_ID = 'CP3P9CS2W'
channels: Dict[str, ChannelInfo]  = dict()


def create_table(web_client: slack.WebClient, channel: str, user: str):
    if channel in channels.keys():
        send_msg(web_client, channel,
                 "Failed to open a game, because there is an unfinished game in this channel!")
        return

    table_id = gameManager.open(user)
    channels[channel] = ChannelInfo(table_id, web_client)
    send_msg(web_client, channel,
             "Successfully opened a game! Everyone is free to join the table.")


def join_table(web_client: slack.WebClient, channel: str, user: str):
    # TODO: use wrapper to check channel
    if channel not in channels.keys():
        send_msg(web_client, channel,
                 "Failed to join the table, because there is no opened game in this channel.")
        return
    table_id = channels[channel].table_id

    pos, nplayer, err = gameManager.join(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)
        return

    send_msg(web_client, channel,
             f"just joined at position {pos}, total player: {nplayer}", user)

    if nplayer == 2:
        send_msg(web_client, channel,
                 'Now you can start a game by replying "start" or wait for more player to join in.')


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
        if not hand['id'].startswith("bot"):
            send_private_msg_in_channel(
                web_client, channel, hand["id"], f"Your hand is {hand['hand']}")
        else:
            send_msg(web_client, channel, f"{hand['id']} has {hand['hand']}")
    send_msg(web_client, channel,
             "Game started! I have send your hand to you personnaly.")
    # threading.Thread(target=gameManager.start_timer,
    #                  args=(table_id,)).start()

def continue_game(web_client: slack.WebClient, channel: str, user: str):
    # TODO: Reduce redundant code
    if channel not in channels.keys():
        send_msg(web_client, channel,
                 "Failed to continue, because there is no opened game in this channel.")
        return
    table_id = channels[channel].table_id
    hands, err = gameManager.continue_game(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)
        return
    for hand in hands:
        if not hand['id'].startswith("bot"):
            send_private_msg_in_channel(
                web_client, channel, hand["id"], f"Your hand is {hand['hand']}")
        else:
            send_msg(web_client, channel, f"{hand['id']} has {hand['hand']}")
    send_msg(web_client, channel,
             "Game started! I have send your hand to you personnaly.")

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
    if err is None:
        send_msg(web_client, channel, f"has raised {chip}", user)
    else:
        send_msg(web_client, channel, err)


def call(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.call(table_id, user)
    if err is None:
        send_msg(web_client, channel, "has called", user)
    else:
        send_msg(web_client, channel, err)


def all_in(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.all_in(table_id, user)
    if err is None:
        send_msg(web_client, channel, "has raised all in", user)
    else:
        send_msg(web_client, channel, err)


def check(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.check(table_id, user)
    if err is None:
        send_msg(web_client, channel, "has checked", user)
    else:
        send_msg(web_client, channel, err)


def fold(web_client: slack.WebClient, channel: str, user: str):
    table_id = channels[channel].table_id
    err = gameManager.fold(table_id, user)
    if err is None:
        send_msg(web_client, channel, f"{user} has folded")
    else:
        send_msg(web_client, channel, err)


def echo_info(web_client: slack.WebClient, channel: str):
    table_id = channels[channel].table_id
    send_msg(web_client, channel, gameManager.get_game_info(table_id))


def send_to_channel_by_table_id(table_id, msg):
    for (channel, info) in channels.items():
        if info.table_id == table_id:
            ts = send_msg(info.client, channel, msg)
            return ts, None
    return None, "table_id not found"


def update_msg_by_table_id(table_id, ts, msg):
    for (channel, info) in channels.items():
        if info.table_id == table_id:
            update_msg(info.client, channel, msg, ts)
            return None
    return "table_id not found"
