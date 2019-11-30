import slack


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


def delete_msg(web_client: slack.WebClient, channel: str, ts: str):
    """Delete a message

    Args:
        web_client (slack.WebClient): web client object
        channel (str): The channel id. e.g. 'C1234567890'
        ts (str): The timestamp of the old message
    """
    web_client.chat_delete(channel=channel, ts=ts)


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


# example payload:
# [
# 	{
# 		"type": "section",
# 		"text": {
# 			"type": "mrkdwn",
# 			"text": ":spades:*5*  :hearts:*7*  :clubs:*A*  :diamonds:*K* :clock12:  :b: :star: :large_blue_circle: :red_circle:"
# 		}
# 	},
# 	{
# 		"type": "divider"
# 	},
# 	{
# 		"type": "section",
# 		"text": {
# 			"type": "mrkdwn",
# 			"text": "*total pot: 1200\t\tlevel: 50/100\t\tbtn: <@Uabcdefg>*"
# 		}
# 	},
# 	{
# 		"type": "divider"
# 	},
# 	{
# 		"type": "section",
# 		"text": {
# 			"type": "mrkdwn",
# 			"text": "<@U122233>($200)  check\n<@Ufds2333>($500)  bet $200\n<@Uiofd234>($330)  :clock12: 49s\n<@Uedi1261>($220)"
# 		}
# 	}
# ]

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
