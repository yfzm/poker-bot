import slack
import os
import ssl as ssl_lib
import certifi
from bots.game import handle_message
import logging
import threading
import asyncio

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


class SyncClient(slack.WebClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._synclock = threading.Lock()

    def api_call(self, *args, **kwargs):
        try:
            self._synclock.acquire()
            res = super().api_call(*args, **kwargs)
        finally:
            self._synclock.release()
        return res


@slack.RTMClient.run_on(event="message")
def test_rtm_client(**payload):

    data = payload["data"]

    # filter bot message
    if "subtype" in data.keys():
        logger.info(f"emit a {data['subtype']} message")
        return

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
    web_client = SyncClient(token=slack_token, loop=asyncio.new_event_loop())
    bot_userid = web_client.auth_test()['user_id']

    rtm_client = slack.RTMClient(token=slack_token, ssl=ssl_context)
    rtm_client.start()
