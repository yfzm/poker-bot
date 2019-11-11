import slack
import os
import ssl as ssl_lib
import certifi
import time
from slackapi.client import *
from bots.game import handle_message


@slack.RTMClient.run_on(event="message")
def test_rtm_client(**payload):
    data = payload["data"]
    web_client = payload["web_client"]

    text = data['text']:
    channel = data['channel']
    ts = data['ts']
    user = data['user']

    handle_message(web_client=web_client, channel=channel, user=user, ts=ts, text=text)


if __name__ == "__main__":
    slack_token = os.environ["SLACK_BOT_TOKEN"]
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    # web_client = slack.WebClient(token=slack_token)
    # ts = send_msg(web_client, "CP3P9CS2W", "test api", user='UPGH1C1PF')
    # time.sleep(5)
    # update_msg(web_client, "CP3P9CS2W", "updated!", ts)
    # update_msg(web_client, "CP3P9CS2W", "update again!", ts)
    # send_private_msg_in_channel(web_client, "CP3P9CS2W", 'UPGH1C1PF', "test api")

    rtm_client = slack.RTMClient(token=slack_token, ssl=ssl_context)
    rtm_client.start()


# payload
# {
#     'channel': 'CP3P9CS2W', 
#     'client_msg_id': 'ef7da782-9247-40b4-...8da60ce45', 
#     'event_ts': '1573485980.042900', 
#     'source_team': 'TPGH1C1D3', 
#     'suppress_notification': False, 
#     'team': 'TPGH1C1D3', 
#     'text': '<@UPJPKD5N2> Hello', 
#     'ts': '1573485980.042900', 
#     'user': 'UPGH1C1PF', 
#     'user_team': 'TPGH1C1D3'
# }