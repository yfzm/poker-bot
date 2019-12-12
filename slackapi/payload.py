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
        username (str): user name
        name_len (int): characters to show the name
        remaining_chip (int): remaining chip of the user
        action (str): the action being taken, should be one of the
            following: check, bet, raise, all-in, fold
            The differences of `bet` and `raise` are that `bet` is
            the first put-chip action, while `raise` is another
            put-chip action against prior `bet`
        chip (int): the chip of an action, only meaningful when
            `action` is `bet`, `raise` or `all-in`
        is_waiting (bool): a flag that indicate if this user is in
            execution position
        countdown (int): the countdown of waiting, only meaningful
            when `is_waiting` is `True`

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


def build_payload(pub_cards: List[str], pot: int, ante: int, btn_username: str, infos: List[str]) -> List[object]:
    ret = [{
        "type": "divider"
    }]

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
            "text": f"*total pot: ${pot}\t\tlevel: ${ante // 2}/${ante}\t\tbtn: {btn_username}*"
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


def build_prompt_payload(cards: List[str], remaining: int, call_needed: int, mini_raise: int):
    """Build prompt payload to tell player their choices. The choices include `check`, `call`,
    `bet`, `all in` and `fold`. Only when `call_needed` = `0`, we give `check` hint. Only when
    `0` < `call_needed` < `remaining`, we give `call` hint. Only when `remaining` > `call_needed`
    or `remaining` > `mini_raise`, we give `bet` option. We always give `all in` and `fold`
    options

    Args:
        cards (List[str]): Player's hand
        remaining (int): The chip that the user own at the time
        call_needed (int): The chip that the user need to call (0 for check)
        mini_raise (int): The minimal chip to raise
    """
    ret = []

    card_str = ""
    for card in cards:
        card_str += card_to_emoji(str(card)) + " "

    actions = ""
    if call_needed == 0:
        actions += "`c`heck, "
    if 0 < call_needed <= remaining:
        actions += f"`c`all ${call_needed}, "
    if remaining > call_needed or remaining > mini_raise:
        actions += f"`b`et [chip num](at least ${mini_raise}), "
    actions += "`a`ll in, or `f`old"

    ret.append({
        "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"It's your turn. Your hand is {card_str}\nYou can choose {actions}"
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
