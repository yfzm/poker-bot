from slackbot.bot import respond_to
from slackbot.bot import listen_to
import re
from libs.manager import gameManager

CHANNEL_ID = 'CP3P9CS2W'


@listen_to('open')
def open(message):
    # TODO: 教slackbot说中文
    def reply_start(s: str):
        message.send(s)
    def reply_status(game, action, playerPos, body):
        message.send(f"action: {action}, player: {playerPos}, body: {body} \n")

    suc = gameManager.prepare(reply_start)
    gameManager.set_ob(reply_status)
    if suc:
        message.send('Wait for people to join. Reply "join" and mention me to join the game')
    else:
        message.reply("There is already a unfinished game!")


# TODO: replace with more interactive api
@respond_to('join', re.IGNORECASE)
def join(message):
    suc, nplayer = gameManager.join(message.user)

    if suc:
        message._client.rtm_send_message(CHANNEL_ID, '{} just joined, total player: {}'.format(message.user["name"], nplayer))
        if nplayer == 2:
            message._client.rtm_send_message(CHANNEL_ID, 'Now you can start a game by replying "start" or wait for more player to join in.')
    else:
        # TODO: give explicit reason
        message.reply("Failed to join game or already in the game.")


def send_to_user_by_name(message, username):
    message._client.rtm_send_message(message._client.find_channel_by_name(username), 'reply test')