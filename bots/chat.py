from slackbot.bot import respond_to
from slackbot.bot import listen_to
import re


@respond_to('hi', re.IGNORECASE)
def hi(message):
    message.reply('I can understand hi or HI!')
    # react with thumb up emoji
    message.react('+1')


@respond_to('who are you?')
def love(message):
    message.reply("I'm a poker robot")


@listen_to('Can someone help me?')
def help(message):
    # Message is replied to the sender (prefixed with @user)
    message.reply('Yes, I can!')

    # Message is sent on the channel
    message.send('I can help everybody!')

    # Start a thread on the original message
    message.reply("Here's a threaded reply", in_thread=True)


@listen_to('test')
def test(message):
    message._client.rtm_send_message(
        message._client.find_channel_by_name("username"), 'reply test')
