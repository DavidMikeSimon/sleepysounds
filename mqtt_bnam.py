#!/usr/bin/python

import config
import json
import time
import math
from decimal import Decimal
from time import mktime
from datetime import datetime
from lib.nightlight.control import nightlight_set, nightlight_on, nightlight_off
from lib.mixer.control import change_volume
from lib.sound.control import play_sound, stop_sound
import paho.mqtt.client as mqtt

# sleep for 1 minute to ensure we have network connectivity on reboot of the Pi, since this is run as a startup script
# TODO: try to make this BETTER than this ugly hack in the future
time.sleep(5)

# define the topics to subscribe to
light_topic = '/nightlight/light/set'
rgb_topic = '/nightlight/light/rgb/set'
brightness_topic = '/nightlight/light/brightness/set'
sound_topic = '/nightlight/sound/set'
volume_topic = '/nightlight/sound/volume/set'
volume_up_topic = '/nightlight/sound/volume/up/set'
volume_down_topic = '/nightlight/sound/volume/down/set'
volume_mute_topic = '/nightlight/sound/volume/mute/set'
play_sound_topic = '/nightlight/sound/play_sound/set'
play_next_sound_topic = '/nightlight/sound/play_sound/next/set'
play_previous_sound_topic = '/nightlight/sound/play_sound/previous/set'

# define the topics to publish state and information to
light_state_topic = '/nightlight/light/state'
brightness_state_topic = '/nightlight/light/brightness/state'
rgb_state_topic = '/nightlight/light/rgb/state'
sound_state_topic = '/nightlight/sound/state'
sound_playlist_topic = '/nightlight/sound/playlist'
volume_state_topic = '/nightlight/sound/volume/state'
play_sound_state_topic = '/nightlight/sound/play_sound/state'
previous_sound_state_topic = '/nightlight/sound/play_sound/previous/state'
next_sound_state_topic = '/nightlight/sound/play_sound/next/state'


# global variables
light_switch_value = '{"action":"off"}'
rgb_value = '{"r":255,"g":0,"b": 200}'
brightness_value = 1
sound_switch_value = '{"action":"off"}'
volume_value = 100
play_sound_value = 'Noise 4'
sound_dictionary = {'Noise 4': '/home/pi/server/sounds/white-noise-4.mp3',
                    'Dryer 2': '/home/pi/server/sounds/dryer-2.mp3',
                    'Fan 2': '/home/pi/server/sounds/fan-2.mp3',
                    'Train 1': 'home/pi/server/sounds/train-1.mp3',
                    'Rain 1': '/home/pi/server/sounds/rain-1.mp3',
                    'Rain 2': '/home/pi/server/sounds/rain-2.mp3',
                    'Rain 3': '/home/pi/server/sounds/rain-3.mp3',
                    'Rain 4': '/home/pi/server/sounds/rain-4.mp3'}

# array containing topics to subscribe to
allTopics = [light_topic, rgb_topic, sound_topic, play_sound_topic,
             play_next_sound_topic, play_previous_sound_topic, volume_topic, volume_up_topic, volume_down_topic]

# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print('Connected with result code: ' + str(rc))
    print(allTopics)
    for topic in allTopics:
        client.subscribe(topic)
        print('subscribed to topic => ' + topic)

# The callback for when a PUBLISH message is received from the server.


def on_message_received(client, userdata, msg):
    # print('Topic: [' + msg.topic + "] - Payload: [" + msg.payload + "]")

    if msg.topic == light_topic:
        handle_set_light_request(payload=msg.payload)
    elif msg.topic == brightness_topic:
        handle_set_brightness_request(payload=msg.payload)
    elif msg.topic == rgb_topic:
        handle_set_rgb_request(payload=msg.payload)
    elif msg.topic == sound_topic:
        handle_set_sound_request(payload=msg.payload)
    elif msg.topic == volume_topic:
        handle_set_volume_request(payload=msg.payload)
    elif msg.topic == play_sound_topic:
        handle_set_play_sound_request(payload=msg.payload)
    elif msg.topic == play_next_sound_topic:
        handle_set_play_next_request()
    elif msg.topic == play_previous_sound_topic:
        handle_set_play_previous_request()
    elif msg.topic == volume_up_topic:
        handle_volume_up_request()
    elif msg.topic == volume_down_topic:
        handle_volume_down_request()
    elif msg.topic == volume_mute_topic:
        handle_volume_mute_request()


# -------------------------------------------------------------------------------------------------------------
# State publish section
# -------------------------------------------------------------------------------------------------------------


def handle_nightlight_switch_state_request():
    client.publish(light_state_topic, light_switch_value, 0, False)

def handle_nightlight_color_state_request():
    client.publish(rgb_state_topic, rgb_value, 0, False)


def handle_nightlight_brightness_state_request():
    client.publish(brightness_state_topic, brightness_value, 0, False)


def handle_whitenoise_volume_state_request():
    client.publish(volume_state_topic, volume_value, 0, False)


def handle_whitenoise_sound_state_request():
    client.publish(play_sound_state_topic, play_sound_value, 0, False)


def handle_whitenoise_switch_state_request():
    client.publish(sound_state_topic, sound_switch_value, 0, False)
    client.publish(sound_playlist_topic, json.dumps(sound_dictionary), 0, False)


def handle_previous_next_state_request(newPrevious, newNext, newCurrent):
    client.publish(previous_sound_state_topic, newPrevious, 0, False)
    client.publish(next_sound_state_topic, newNext, 0, False)
    client.publish(play_sound_state_topic, newCurrent, 0, False)

# -------------------------------------------------------------------------------------------------------------
# Sound set section
# -------------------------------------------------------------------------------------------------------------


def handle_set_play_next_request():
    global play_sound_value
    keyList = sorted(sound_dictionary.keys())
    for i, v in enumerate(keyList):
        if v == play_sound_value:
            handle_previous_next_state_request(keyList[i], keyList[i+2], keyList[i+1])
            play_sound_value = keyList[i+1]
            stop_sound()
            play_sound(sound_dictionary[play_sound_value])
            change_volume(volume_value)
    handle_whitenoise_sound_state_request()


def handle_set_play_previous_request():
    global play_sound_value
    keyList = sorted(sound_dictionary.keys())
    for i, v in enumerate(keyList):
        if v == play_sound_value:
            handle_previous_next_state_request(keyList[i-2], keyList[i], keyList[i-1])
            play_sound_value = keyList[i-1]
            stop_sound()
            play_sound(sound_dictionary[play_sound_value])
            change_volume(volume_value)
    handle_whitenoise_sound_state_request()


def handle_set_volume_request(payload):
    global volume_value
    if payload == volume_value:
        return
    else:
        volume_value = int(Decimal(json.loads(payload)) * 100)
        change_volume(volume_value)
    handle_whitenoise_volume_state_request()


def handle_volume_up_request():
    change_volume((volume_value+5))


def handle_volume_down_request():
    change_volume((volume_value-5))


def handle_volume_mute_request():
    change_volume(0)


def handle_set_play_sound_request(payload):
    global play_sound_value
    if payload == play_sound_value:
        return
    else:
        stop_sound()
        play_sound_value = payload
    handle_whitenoise_sound_state_request()


def handle_set_sound_request(payload):
    global sound_switch_value
    jsonPayload = json.loads(payload)
    if jsonPayload["action"] == 'off':
        sound_switch_value = '{"action":"off"}'
        stop_sound()
    else:
        stop_sound()
        sound_switch_value = '{"action":"on"}'
        play_sound(sound_dictionary[play_sound_value])
        change_volume(volume_value)
    handle_whitenoise_switch_state_request()

# -------------------------------------------------------------------------------------------------------------
# Light set section
# -------------------------------------------------------------------------------------------------------------


def handle_set_brightness_request(payload):
    global brightness_value
    if payload == brightness_value:
        return
    else:
        brightness_value = payload
        handle_nightlight_brightness_state_request


def handle_set_light_request(payload):
    global light_switch_value
    jsonPayload = json.loads(payload)
    if jsonPayload["action"] == 'off':
        light_switch_value = '{"action":"off"}'
        nightlight_set(0, 0, 0, 0.5)
        nightlight_on()
        nightlight_off()
    else:
        nightlight_off()
        light_switch_value = '{"action":"on"}'
        jsonPayload = json.loads(rgb_value)
        nightlight_set(red=jsonPayload["r"], green=jsonPayload["g"],
                       blue=jsonPayload["b"], brightness=brightness_value)
        nightlight_on()
    handle_nightlight_switch_state_request()


def handle_set_rgb_request(payload):
    global rgb_value
    if payload == rgb_value:
        return
    else:
        rgb_value = payload
    handle_nightlight_color_state_request

# -------------------------------------------------------------------------------------------------------------


client = mqtt.Client('baby-nightlight')

#client.tls_set(ca_certs=config.caBundlePath, certfile=config.certFilePath, keyfile=config.keyFilePath)
#client.username_pw_set(config.username, config.password)
client.connect('192.168.1.100')

client.on_connect = on_connect
client.on_message = on_message_received

client.loop_forever()
