from typing import List


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


def build_info_str(username: str, name_len: int, remaining_chip: int, action: str,
                   chip: int, is_waiting: bool, countdown: int) -> str:
    """Build a string to explain action of a user

    Args:
        user (str): user id
        remaining_chip (int): remaining chip of the user
        action (str): the action being taken, should be one of the
            following: check, bet, raise, all-in, fold
            The differences of `bet` and `raise` are that `bet` is
            the first put-chip action, while `raise` is another
            put-chip action against prior `bet`
        chip (int): the chip of an action, only meaningful when
            `action` is `bet`, `raise` or `all-in`
        is_wating (bool): a flag that indicate if this user is in
            execution postion
        countdown (int): the countdown of waiting, only meaningful
            when `is_wating` is `True`

    Return:
        info_str (str): a string to explain action of a user
    """
    info = f"{username:{name_len}} (${str(remaining_chip) + ')':<5} {action}"
    if action in ("bet", "raise", "all-in"):
        info += f" ${chip}    "
    if is_waiting:
        info += f"{countdown}s"
        info = "-> " + info
    else:
        info = "   " + info
    return info


def build_payload(pub_cards: List[str], pot: int, ante: int, btn_userid: str, infos: List[str]) -> List[object]:
    ret = []

    ret.append({
        "type": "divider"
    })

    if len(pub_cards) > 0:
        card_str = ""
        for card in pub_cards:
            card_str += card_to_emoji(str(card)) + "  "
        ret.append({
            "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": card_str
                    }
        })

    ret.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*total pot: ${pot}\t\tlevel: ${ante // 2}/${ante}\t\tbtn: <@{btn_userid}>*"
        }
    })

    info_str = "```"
    for info in infos:
        info_str += info + "\n"
    info_str += "```"
    ret.append({
        "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": info_str
                }
    })
    return ret


def build_prompt_payload(cards: List[str], remaining: int, call_needed: int):
    ret = []

    card_str = ""
    for card in cards:
        card_str += card_to_emoji(str(card)) + " "

    action = "*check*" if call_needed == 0 else f"*call* ${call_needed}"
    prompt = f"you can {action}, *bet* (*all* for all-in) or *fold*"

    ret.append({
        "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your hand: {card_str}   Your chips: ${remaining}\n{prompt}"
                }
    })

    return ret


if __name__ == "__main__":
    import os
    import slack
    slack_token = os.environ["SLACK_BOT_TOKEN"]
    web_client = slack.WebClient(token=slack_token)
    # p1 = build_info_str("UPGH1C1PF", 200, "check", 0, False, 0)
    # p2 = build_info_str("UPGH1C1PF", 400, "bet", 40, False, 0)
    # p3 = build_info_str("UPGH1C1PF", 300, "", 0, True, 33)

    # ts = send_msg(web_client, "CP3P9CS2W", None, None,
    #               build_payload(["Qs", "8d", "5c"], 1200, 20, "UPGH1C1PF", [p1, p2, p3]))
    # time.sleep(3)
    # update_msg(web_client, channel="CP3P9CS2W", ts=ts, msg=None,
    #            user=None, blocks=build_payload(["As", "Ad", "Ac"], 1200, 20, "UPGH1C1PF", [p1, p2, p3]))
    # web_client.chat_postMessage(channel="CP3P9CS2W",
    #                             blocks=build_payload(["Qs", "8d", "5c"], 1200, 20, "UPGH1C1PF", [p1, p2, p3]))
