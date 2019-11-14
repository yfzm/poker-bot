import slack
from slackbot.bot import respond_to
from slackbot.bot import listen_to
import re
from libs.manager import gameManager
from .message_helper import *
import threading
from slackapi.client import *

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

def handle_message(web_client: slack.WebClient, channel: str, user: str, ts: str, text: str, mentioned: bool):
    if text == "open":
        create_table(web_client, channel, user)
    elif text == "join":
        join_table(web_client, channel, user)
    elif text == "start":
        start_game(web_client, channel, user)
    else:
        if mentioned:
            send_msg(web_client, channel, HELP_MSG, user)


# TODO: 教slackbot说中文
# CHANNEL_ID = 'CP3P9CS2W'
g_games = {}


def create_table(web_client: slack.WebClient, channel: str, user: str):
    if channel in g_games.keys():
        message.reply("Failed to open a game, because there is an unfinished game in this channel!")
        return
    
    table_id = gameManager.open(user)
    g_games[channel] = {
        "table_id": table_id,
        "client": web_client
    }
    send_msg(web_client, channel, "Successfully opened a game! Everyone is free to join the table.")


def join_table(web_client: slack.WebClient, channel: str, user: str):
    # TODO: use wrapper to check channel
    if channel not in g_games.keys():
        send_msg(web_client, channel, "Failed to join the table, because there is no opened game in this channel.")
        return
    table_id = g_games[channel]["table_id"]

    pos, nplayer, err = gameManager.join(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)
        return

    send_msg(web_client, channel, f"just joined at position {pos}, total player: {nplayer}", user)

    if nplayer == 2:
        send_msg(web_client, channel,
            'Now you can start a game by replying "start" or wait for more player to join in.')


def start_game(web_client: slack.WebClient, channel: str, user: str):
    if channel not in g_games.keys():
        send_msg(web_client, channel, "Failed to start, because there is no opened game in this channel.")
        return
    table_id = g_games[channel]["table_id"]
    hands, err = gameManager.start(table_id, user)
    if err is not None:
        send_msg(web_client, channel, err)
        return
    for hand in hands:
        send_private_msg_in_channel(web_client, channel, hand["id"], f"Your hand is {hand['hand']}")
    send_msg(web_client, channel, "Game started! I have send your hand to you personnaly.")
    threading.Thread(target=gameManager.timer_function, args=(table_id,)).start()


@listen_to(r'^r(\d+)')
def raise_(message, chip):
    user = message.user["name"]
    if gameManager.raise_(user, int(chip)):
        message.reply(f"{user} has raised {chip}")
    else:
        message.reply("raise wrong!")

@listen_to(r'^b(\d+)')
def bet(message, chip):
    user = message.user["name"]
    if gameManager.bet(user, int(chip)):
        message.reply(f"{user} has raised {chip}")
    else:
        message.reply("bet wrong!")

@listen_to('^ca')
def call(message):
    user = message.user["name"]
    if gameManager.check(user):
        message.reply(f"{user} has checked")
    else:
        message.reply("call wrong!")

@listen_to('^a')
def all_in(message):
    user = message.user["name"]
    if gameManager.check(user):
        message.reply(f"{user} has checked")
    else:
        message.reply("all in wrong!")

@listen_to('^c')
def check(message):
    user = message.user["name"]
    if gameManager.check(user):
        message.reply(f"{user} has checked")
    else:
        message.reply("check wrong!")


@listen_to('^f')
def fold(message):
    user = message.user["name"]
    if gameManager.fold(user):
        message.reply(f"{user} has folded")
    else:
        message.reply("fold wrong!")


def send_to_channel_by_table_id(table_id, msg):
    for (channel, info) in g_games.items():
        if info['table_id'] == table_id:
            ts = send_msg(info['client'], channel, msg)
            return ts, None
    return None, "table_id not found"

def update_msg_by_table_id(table_id, ts, msg):
    for (channel, info) in g_games.items():
        if info['table_id'] == table_id:
            update_msg(info['client'], channel, msg, ts)
            return None
    return "table_id not found"

def get_user_name_by_id(user_id):
    return g_user_id2name[user_id]