import slack
from slack.errors import SlackApiError


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


def get_username(web_client: slack.WebClient, user: str) -> str:
    try:
        response = web_client.users_info(user=user)
        return response['user']['real_name']
    except SlackApiError:
        return "USER404"


if __name__ == "__main__":
    import os
    import slack
    slack_token = os.environ["SLACK_BOT_TOKEN"]
    web_client = slack.WebClient(token=slack_token)
    # print(get_username(web_client, "UPGH1C1PF"))
    # web_client.files_upload(content="abc", channels=["CP3P9CS2W"])
    web_client.chat_postMessage(channel="CP3P9CS2W", text="```abc```")

    # ts = send_msg(web_client, "CP3P9CS2W", None, None,
    #               build_payload(["Qs", "8d", "5c"], 1200, 20, "UPGH1C1PF", [p1, p2, p3]))
