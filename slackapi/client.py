import slack


def send_msg(web_client: slack.WebClient, channel: str, msg: str, user=None) -> str:
    """Send a message to a channel

    Args:
        web_client (slack.WebClient): web client object
        channel (str): The channel id. e.g. 'C1234567890'
        msg (str): The message you'd like to share. e.g. 'Hello world'
            text is not required when presenting blocks.
        user (str) optional: If provided, '@user-name ' will be added before msg

    Return:
        ts (str): The timestamp of this message
    """
    if user is not None:
        msg = f"<@{user}> " + msg
    slack_response = web_client.chat_postMessage(channel=channel, text=msg)
    ts = slack_response.data["ts"]
    return ts

def update_msg(web_client: slack.WebClient, channel: str, msg: str, ts: str, user=None):
    """Update a message

    Args:
        web_client (slack.WebClient): web client object
        channel (str): The channel id. e.g. 'C1234567890'
        msg (str): The new message you'd like to update to
        ts (str): The timestamp of the old message
        user (str) optional: If provided, '@user-name ' will be added before msg
    """
    if user is not None:
        msg = f"<@{user}> " + msg
    web_client.chat_update(channel=channel, ts=ts, text=msg)

def send_private_msg_in_channel(web_client: slack.WebClient, channel: str, user: str, msg: str):
    """Sends an ephemeral message to a user in a channel.

    Args:
        web_client (slack.WebClient): web client object
        channel (str): The channel id. e.g. 'C1234567890'
        user (str): The id of user who should see the message. e.g. 'U0BPQUNTA'
        msg (str): The message you'd like to share. e.g. 'Hello world'
            text is not required when presenting blocks.
    """
    web_client.chat_postEphemeral(channel=channel, user=user, text=msg)

def get_mentioned_string(user: str) -> str:
    """Get mentioned format of a user: @username

    Args:
        user (str): user id
    
    Return:
        mentioned_user_string (str): mentioned string
    """
    return f"<@{user}>"

# slack_response data
# {
#     'channel': 'CP3P9CS2W', 
#     'message': {
#         'bot_id': 'BP53KL083', 
#         'subtype': 'bot_message', 
#         'text': '<@UPGH1C1PF> test api', 
#         'ts': '1573487677.043700', 
#         'type': 'message', 
#         'username': 'Poker-bot'
#     }, 
#     'ok': True, 
#     'ts': '1573487677.043700'
# }