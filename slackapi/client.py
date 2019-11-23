from threading import Lock
from functools import wraps

import slack

GLOCK = Lock()


def synchronized(foo):
    @wraps(foo)
    def wrapper(*arg, **xarg):
        with GLOCK:
            return foo(*arg, **xarg)
    return wrapper


@synchronized
def send_msg(web_client: slack.WebClient, channel: str, msg: str, user=None, blocks=None) -> str:
    """Send a message to a channel

    Args:
        web_client (slack.WebClient): web client object
        channel (str): The channel id. e.g. 'C1234567890'
        msg (str): The message you'd like to share. e.g. 'Hello world'
            text is not required when presenting blocks.
        user (str) optional: If provided, '@user-name ' will be added before msg
        blocks (List[Object]) optional: If provided, `msg` and `user` will be emitted
            blocks can be used for complex message, see more on
            https://api.slack.com/block-kit/building

    Return:
        ts (str): The timestamp of this message
    """
    if blocks is None:
        if user is not None:
            msg = f"<@{user}> " + msg
        slack_response = web_client.chat_postMessage(channel=channel, text=msg)
    else:
        slack_response = web_client.chat_postMessage(
            channel=channel, blocks=blocks)
    ts = slack_response.data["ts"]
    return ts


@synchronized
def update_msg(web_client: slack.WebClient, channel: str, msg: str, ts: str, user=None, blocks=None):
    """Update a message

    Args:
        web_client (slack.WebClient): web client object
        channel (str): The channel id. e.g. 'C1234567890'
        msg (str): The new message you'd like to update to
        ts (str): The timestamp of the old message
        user (str) optional: If provided, '@user-name ' will be added before msg
        blocks (List[Object]) optional: If provided, `msg` and `user` will be emitted
    """
    if blocks is None:
        if user is not None:
            msg = f"<@{user}> " + msg
        web_client.chat_update(channel=channel, ts=ts, text=msg)
    else:
        web_client.chat_update(channel=channel, ts=ts, blocks=blocks)


@synchronized
def send_private_msg_in_channel(web_client: slack.WebClient, channel: str, user: str, msg: str, blocks=None):
    """Sends an ephemeral message to a user in a channel.

    Args:
        web_client (slack.WebClient): web client object
        channel (str): The channel id. e.g. 'C1234567890'
        user (str): The id of user who should see the message. e.g. 'U0BPQUNTA'
        msg (str): The message you'd like to share. e.g. 'Hello world'
            text is not required when presenting blocks.
        blocks (List[Object]) optional: If provided, `msg` will be emitted
    """
    if blocks is None:
        web_client.chat_postEphemeral(channel=channel, user=user, text=msg)
    else:
        web_client.chat_postEphemeral(
            channel=channel, user=user, blocks=blocks)
