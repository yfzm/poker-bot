from slackbot.bot import respond_to
from slackbot.bot import listen_to
import re
from libs.manager import gameManager

@listen_to('start game')
def start_game(message):
    suc = gameManager.prepare()

    if suc:
        message.send('Wait for people to join. Reply "join" and mention me to join the game')
    else:
        message.reply("There is already a unfinished game!")


@respond_to('join', re.IGNORECASE)
def join(message):
    message.reply('unimplemented!')
