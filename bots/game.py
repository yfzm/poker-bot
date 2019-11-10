from slackbot.bot import respond_to
from slackbot.bot import listen_to
import re
from libs.manager import gameManager
from .message_helper import *

# TODO: 教slackbot说中文
# CHANNEL_ID = 'CP3P9CS2W'
g_games = {}
g_user_id2name = {}

@listen_to('open')
def open(message):
    channel_id = get_channel(message)
    if channel_id in g_games.keys():
        message.reply("Failed to open a game, because there is an unfinished game in this channel!")
        return
    
    user_id = get_user_id(message)
    user_name = get_user_name(message)

    table_id = gameManager.open(user_id)

    g_user_id2name[user_id] = user_name
    g_games[channel_id] = {
        "table_id": table_id,
        "clinet": message._client
    }

    message.send(
"""Successfully opened a game! Everyone is free to join the table.
Reply "join" to sit at the table:
r  for raise,
c  for check,
f  for fold.
a  for all in
ca for call
b  for bet""")


# TODO: replace with more interactive api
@listen_to(r'^join')
def join(message):
    # TODO: use wrapper to check channel_id
    channel_id = get_channel(message)
    if channel_id not in g_games.keys():
        message.reply("Failed to join the table, because there is no opened game in this channel.")
        return
    table_id = g_games[channel_id]["table_id"]
    user_id = get_user_id(message)

    pos, nplayer, err = gameManager.join(table_id, user_id)
    if err is not None:
        message.reply(err)
        return

    message.reply(
        '{} just joined at position {}, total player: {}'.format(message.user["name"], pos, nplayer))

    if nplayer == 2:
        message.reply(
            'Now you can start a game by replying "start" or wait for more player to join in.')


@listen_to("^start")
def start(message):
    channel_id = get_channel(message)
    if channel_id not in g_games.keys():
        message.reply("Failed to start, because there is no opened game in this channel.")
        return
    table_id = g_games[channel_id]["table_id"]
    user_id = get_user_id(message)
    hands, err = gameManager.start(table_id, user_id)
    if err is not None:
        message.reply(err)
        return
    for hand in hands:
        send_to_user_by_name(message, g_user_id2name[hand["id"]], "Your hand is {}".format(hand["hand"]))
    message.send("Game started! I have send your hand to you personnaly.")


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
    for (channel_id, info) in g_games:
        if info['table_id'] == table_id:
            info['client'].rtm_send_message(channel_id, msg)
            return None
    return "table_id not found"
