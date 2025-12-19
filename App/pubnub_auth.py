from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.models.consumer.v3.channel import Channel
import os

CHANNEL_NAME = os.getenv('PUBNUB_CHANNEL')

def init_pubnub(uuid):
    if not uuid:
        raise ValueError("UUID cannot be empty or None.")
    
    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = os.getenv('PUBNUB_SUBSCRIBE_KEY')
    pnconfig.publish_key = os.getenv('PUBNUB_PUBLISH_KEY')
    pnconfig.secret_key = os.getenv('PUBNUB_SECRET_KEY')
    pnconfig.uuid = uuid
    
    return PubNub(pnconfig)

def generate_token(user_id, user_access, ttl=60):
    try:
        pubnub = init_pubnub(user_id)

        if user_access == "grant_read_write":
            token = grant_read_write_access_token(user_id, pubnub, ttl)
        elif user_access == "grant_read":
            token = grant_read_access_token(user_id, pubnub, ttl)
        else:
            print("Invalid access type")
            token = None
        
        return token
    except Exception as e:
        print(f"Error generating token: {e}")
        return None
    
def refresh_token(user_id, user_access, ttl=60):
    try:
        new_token = generate_token(user_id, user_access, ttl)
        return new_token
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None
    
def grant_read_write_access_token(user_id, pubnub, ttl):
    print(f"Granting read and write access token for: {user_id}")
    envelope = pubnub.grant_token() \
        .channels([Channel.id(CHANNEL_NAME).read().write()]) \
        .authorized_uuid(user_id) \
        .ttl(ttl) \
        .sync()
    
    token = envelope.result.token
    return token

def grant_read_access_token(user_id, pubnub, ttl):
    print(f"Granting read access token for: {user_id}")
    envelope = pubnub.grant_token() \
        .channels([Channel.id(CHANNEL_NAME).read()]) \
        .authorized_uuid(user_id) \
        .ttl(ttl) \
        .sync()
    
    token = envelope.result.token
    return token