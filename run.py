import slack
import os
import ssl as ssl_lib
import certifi
from bots.game import handle_message


@slack.RTMClient.run_on(event="message")
def test_rtm_client(**payload):

    data = payload["data"]

    # filter bot message
    if "subtype" in data.keys():
        print(f"emit a {data['subtype']} message")
        return

    web_client = payload["web_client"]

    text = data['text']
    channel = data['channel']
    ts = data['ts']
    user = data['user']

    mentioned = False
    if f'<@{bot_userid}>' in text:
        mentioned = True

    handle_message(web_client=web_client, channel=channel,
                   user=user, ts=ts, text=text, mentioned=mentioned)


if __name__ == "__main__":
    slack_token = os.environ["SLACK_BOT_TOKEN"]
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    web_client = slack.WebClient(token=slack_token)
    bot_userid = web_client.auth_test()['user_id']

    rtm_client = slack.RTMClient(token=slack_token, ssl=ssl_context)
    rtm_client.start()
