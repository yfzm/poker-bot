def get_channel(message):
    return message.body['channel']

def get_user_id(message):
    return message.user['id']

def get_user_name(message):
    return message.user['name']

def send_to_channel_by_id(message, channel_id, msg):
    message._client.rtm_send_message(channel_id, msg)

def send_to_user_by_name(message, username, msg):
    message._client.rtm_send_message(
        message._client.find_channel_by_name(username), msg)
