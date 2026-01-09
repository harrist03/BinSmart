import RPi.GPIO as GPIO
import time
import os
from dotenv import load_dotenv
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

load_dotenv()

TRIG_PIN = 23
ECHO_PIN = 24

GREEN_LED_PIN = 17
RED_LED_PIN = 27

BIN_FULL_THRESHOLD = 7
PUBLISH_CHANGE_THRESHOLD = 2.0
MIN_PUBLISH_INTERVAL = 5

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
GPIO.setup(RED_LED_PIN, GPIO.OUT)

GPIO.output(GREEN_LED_PIN, False)
GPIO.output(RED_LED_PIN, False)

BIN_ID = os.getenv("PUBNUB_BIN_ID")
PUBNUB_CHANNEL = os.getenv("PUBNUB_CHANNEL")

def init_pubnub():
    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = os.getenv("PUBNUB_SUBSCRIBE_KEY")
    pnconfig.publish_key = os.getenv("PUBNUB_PUBLISH_KEY")
    pnconfig.secret_key = os.getenv("PUBNUB_SECRET_KEY")
    pnconfig.uuid = BIN_ID
    return PubNub(pnconfig)


pubnub = init_pubnub()

def measure_distance():
    GPIO.output(TRIG_PIN, False)
    time.sleep(0.05)

    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    timeout = time.time() + 0.02
    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()
        if time.time() > timeout:
            return None

    timeout = time.time() + 0.02
    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()
        if time.time() > timeout:
            return None

    elapsed = stop_time - start_time
    distance_cm = (elapsed * 34300) / 2

    return distance_cm

def update_leds(distance):
    if distance <= BIN_FULL_THRESHOLD:
        GPIO.output(RED_LED_PIN, True)
        GPIO.output(GREEN_LED_PIN, False)
    else:
        GPIO.output(RED_LED_PIN, False)
        GPIO.output(GREEN_LED_PIN, True)

def should_publish(current_distance, last_published_distance, last_publish_time):
    if last_published_distance is None:
        return True

    time_since_last_publish = time.time() - last_publish_time
    if time_since_last_publish < MIN_PUBLISH_INTERVAL:
        return False

    distance_change = abs(current_distance - last_published_distance)
    if distance_change >= PUBLISH_CHANGE_THRESHOLD:
        return True

    was_full = last_published_distance <= BIN_FULL_THRESHOLD
    is_full = distance <= BIN_FULL_THRESHOLD

    if was_full != is_full:
        return True

    return False

def publish_to_pubnub(distance):
    try:
        message = {
            'bin_id': int(BIN_ID),
            'distance': round(distance, 2)
        }
        publish_message = pubnub.publish().channel(PUBNUB_CHANNEL).message(message).sync()
        if publish_message.status.is_error():
            print(f"PubNub Error: {publish_message.status.error_data}")
            return False
        else:
            print(f"Published to PubNub: {message}")
            return True
    except Exception as e:
        print(f"Error publishing to pubnub: {e}")
        return False


try:
    last_published_distance = None
    last_publish_time = 0
    while True:
        distance = measure_distance()
        if distance is not None:
            update_leds(distance)

            if should_publish(distance, last_published_distance, last_publish_time):
                if publish_to_pubnub(distance):
                    last_published_distance = distance
                    last_publish_time = time.time()
                    print("Distance: " + str(distance))
        else:
            print("Timeout / invalid reading")

        time.sleep(3)

except KeyboardInterrupt:
    pass

finally:
    GPIO.cleanup()
    pubnub.stop()