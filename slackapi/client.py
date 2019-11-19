import slack
from typing import List


def send_msg(web_client: slack.WebClient, channel: str, msg: str, user=None, blocks=None) -> str:
    """Send a message to a channel

    Args:
        web_client (slack.WebClient): web client object
        channel (str): The channel id. e.g. 'C1234567890'
        msg (str): The message you'd like to share. e.g. 'Hello world'
            text is not required when presenting blocks.
        user (str) optional: If provided, '@user-name ' will be added before msg
        blocks (List[Object]) optional: If provided, `msg` and `user` will be emitted
            blocks can be used for complex message, see more at 
            https://api.slack.com/block-kit/building

    Return:
        ts (str): The timestamp of this message
    """
    if blocks is None:
        if user is not None:
            msg = f"<@{user}> " + msg
        slack_response = web_client.chat_postMessage(channel=channel, text=msg)
    else:
        slack_response = web_client.chat_postMessage(channel=channel, blocks=blocks)
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

kinds = {
    "s": ":spades:",
    "h": ":hearts:",
    "c": ":clubs:",
    "d": ":diamonds:"
}

def card_to_emoji(card: str) -> str:
    """convert card string to emoji

    Args:
        card (str): card string, for example: As, 2c, Td
    """
    kind = kinds[card[1]]
    num = card[0]
    if num == "T":
        num = "10"
    return f"{kind}*{num}*"

def build_info_str(user: str, remainning_chip: int, action: str, chip: int, is_waiting: bool, countdown: int) -> str:
    """Build a string to explain action of a user

    Args:
        user (str): user id
        remainning_chip (int): remainning chip of the user
        action (str): the action being taken, should be one of the
            following: check, bet, raise, all-in, fold
            The differences of `bet` and `raise` are that `bet` is
            the first put-chip action, while `raise` is another
            put-chip action against prior `bet`
        chip (int): the chip of an action, only meanningful when 
            `action` is `bet`, `raise` or `all-in`
        is_wating (bool): a flag that indicate if this user is in 
            execution postion
        countdown (int): the countdown of waiting, only meanningful
            when `is_wating` is `True`
    
    Return:
        info_str (str): a string to explain action of a user
    """
    info = f"<@{user}> (${remainning_chip})  {action} "
    if action in ("bet", "raise", "all-in"):
        info += f"${chip}    "
    if is_waiting:
        info += f":clock12: {countdown}s"
    return info

def build_payload(pub_cards: List[str], pot: int, ante: int, btn_userid: str, infos: List[str]) -> List[object]:
    ret = []
    if len(pub_cards) > 0:
        card_str = ""
        for card in pub_cards:
            card_str += card_to_emoji(card) + "  "
        ret.append({
            "type": "section",
		    "text": {
			    "type": "mrkdwn",
			    "text": card_str
            }
        })
        ret.append({
            "type": "divider"
        })

    ret.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*total pot: ${pot}\t\tlevel: ${ante // 2}/${ante}\t\tbtn: <@{btn_userid}>*"
        }
	})
    ret.append({
        "type": "divider"
    })

    info_str = ""
    for info in infos:
        info_str += info + "\n"
    ret.append({
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": info_str
		}
	})
    return ret

if __name__ == "__main__":
    import os
    import time
    slack_token = os.environ["SLACK_BOT_TOKEN"]
    web_client = slack.WebClient(token=slack_token)
    p1 = build_info_str("UPGH1C1PF", 200, "check", 0, False, 0)
    p2 = build_info_str("UPGH1C1PF", 400, "bet", 40, False, 0)
    p3 = build_info_str("UPGH1C1PF", 300, "", 0, True, 33)

    ts = send_msg(web_client, "CP3P9CS2W", None, None, build_payload(["Qs", "8d", "5c"], 1200, 20, "UPGH1C1PF", [p1, p2, p3]))
    time.sleep(3)
    update_msg(web_client, channel="CP3P9CS2W", ts=ts, msg=None, user=None, blocks=build_payload(["As", "Ad", "Ac"], 1200, 20, "UPGH1C1PF", [p1, p2, p3]))
    # web_client.chat_postMessage(channel="CP3P9CS2W", blocks=build_payload(["Qs", "8d", "5c"], 1200, 20, "UPGH1C1PF", [p1, p2, p3]))

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