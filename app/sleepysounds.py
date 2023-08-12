#!/usr/bin/env python

import config
import json
import os
import time
from decimal import Decimal

import paho.mqtt.client as mqtt
from just_playback import Playback

playback = Playback()
playback.loop_at_end(True)

# define the topics to subscribe to
sound_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/set'
volume_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/volume/set'
volume_up_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/volume/up/set'
volume_down_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/volume/down/set'
play_sound_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/set'
play_next_sound_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/next/set'
play_previous_sound_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/previous/set'

# define the topics to publish state and information to
sound_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/state'
sound_playlist_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/playlist'
volume_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/volume/state'
play_sound_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/state'
previous_sound_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/previous/state'
next_sound_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/next/state'
status_topic = '/'+config.unitTopic+'/'+config.clientId+'/state'

allTopics = [
    sound_topic,
    play_sound_topic,
    play_next_sound_topic,
    play_previous_sound_topic,
    volume_topic,
    volume_up_topic,
    volume_down_topic
]


class UnitStatus:
   'Common base class for all settings'
   def __init__(self, sound_status, sound_setting, volume_setting):
        self.soundStatus = sound_status
        self.soundSetting = sound_setting
        self.volumeSetting = volume_setting

global_status = UnitStatus("off", None, 100)

sound_dictionary = { os.path.splitext(fn)[0]: fn for fn in os.listdir(config.soundsDir) }

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print('Connected with result code: ' + str(rc))
    print(allTopics)
    for topic in allTopics:
        client.subscribe(topic)
        print('subscribed to topic => ' + topic)
    handle_status()

# The callback for when a PUBLISH message is received from the server.
def on_message_received(client, userdata, msg):
    if msg.topic == sound_topic:
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


# -------------------------------------------------------------------------------------------------------------
# State publish section
# -------------------------------------------------------------------------------------------------------------

def handle_status():
    client.publish(status_topic, json.dumps(global_status), 0, False)

def handle_whitenoise_volume_state_request():
    client.publish(volume_state_topic, json.dumps(global_status.volumeSetting), 0, False)

def handle_whitenoise_sound_state_request():
    client.publish(play_sound_state_topic, json.dumps(global_status.soundSetting), 0, False)

def handle_whitenoise_switch_state_request():
    client.publish(sound_state_topic, json.dumps(global_status.soundStatus), 0, False)
    client.publish(sound_playlist_topic, json.dumps(sound_dictionary), 0, False)

def handle_previous_next_state_request(newPrevious, newNext, newCurrent):
    client.publish(previous_sound_state_topic, newPrevious, 0, False)
    client.publish(next_sound_state_topic, newNext, 0, False)
    client.publish(play_sound_state_topic, newCurrent, 0, False)

# -------------------------------------------------------------------------------------------------------------
# Sound set section
# -------------------------------------------------------------------------------------------------------------


def play_sound(file):
    playback.load_file(os.path.join(config.soundsDir, file))
    playback.play()


def handle_set_play_next_request():
    keyList = sorted(sound_dictionary.keys())
    for i, v in enumerate(keyList):
        if v == global_status.soundSetting:
            handle_previous_next_state_request(keyList[i], keyList[i+2], keyList[i+1])
            global_status.soundSetting = keyList[i+1]
            play_sound(sound_dictionary[global_status.soundSetting])
    handle_whitenoise_sound_state_request()


def handle_set_play_previous_request():
    keyList = sorted(sound_dictionary.keys())
    for i, v in enumerate(keyList):
        if v == global_status.soundSetting:
            handle_previous_next_state_request(keyList[i-2], keyList[i], keyList[i-1])
            global_status.soundSetting = keyList[i-1]
            play_sound(sound_dictionary[global_status.soundSetting])
    handle_whitenoise_sound_state_request()


def change_volume(vol):
    if vol < 0:
        vol = 0
    elif vol > 100:
        vol = 100

    global_status.volumeSetting = vol
    playback.set_volume(vol/100.0)
    handle_whitenoise_volume_state_request()


def handle_set_volume_request(payload):
    change_volume(int(Decimal(json.loads(payload)) * 100))


def handle_volume_up_request():
    change_volume(global_status.volumeSetting+5)


def handle_volume_down_request():
    change_volume(global_status.volumeSetting-5)


def handle_set_play_sound_request(payload):
    val = json.loads(payload)
    sound_name = val["action"]
    global_status.soundSetting = sound_name
    play_sound(sound_dictionary[global_status.soundSetting])
    handle_whitenoise_sound_state_request()


def handle_set_sound_request(payload):
    jsonPayload = json.loads(payload)
    if jsonPayload["action"] == 'off':
        playback.stop()
        global_status.soundStatus = "off"
    else:
        play_sound(sound_dictionary[global_status.soundSetting])
        global_status.soundStatus = "on"
    handle_whitenoise_switch_state_request()


def main():
    playback.load_file(os.path.join(config.soundsDir, list(sound_dictionary.values())[0]))
    playback.play()

    while True:
        time.sleep(2)
        print(f"{playback.curr_pos} of {playback.duration}")

    #  client = mqtt.Client(client_id=config.clientId)

    #  client.username_pw_set(config.username, config.password)
    #  client.connect(config.mqttHost, config.mqttPort, config.mqttKeepAlive)

    #  client.on_connect = on_connect
    #  client.on_message = on_message_received

    #  client.loop_forever()


if __name__ == "__main__":
    main()
