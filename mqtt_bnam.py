#!/usr/bin/python

import config
import json
import time
import math
import sqlite3
import paho.mqtt.client as mqtt
from decimal import Decimal
from time import mktime
from datetime import datetime
from lib.nightlight.control import nightlight_set, nightlight_on, nightlight_off
from lib.mixer.control import change_volume
from lib.sound.control import play_sound, stop_sound

class UnitStatus:
   'Common base class for all settings'
   def __init__(self, light_status, rgb_setting, rgb_brightness, sound_status, sound_setting, volume_setting):
        self.lightStatus = light_status
        self.rgbSetting = rgb_setting
        self.rgbBrightness = rgb_brightness
        self.soundStatus = sound_status
        self.soundSetting = sound_setting
        self.volumeSetting = volume_setting

# sleep for 1 minute to ensure we have network connectivity on reboot of the Pi, since this is run as a startup script
# TODO: try to make this BETTER than this ugly hack in the future
time.sleep(60)

# define the topics to subscribe to
light_topic = '/'+config.unitTopic+'/'+config.clientId+'/nightlight/set'
rgb_topic = '/'+config.unitTopic+'/'+config.clientId+'/nightlight/rgb/set'
brightness_topic = '/'+config.unitTopic+'/'+config.clientId+'/nightlight/brightness/set'
sound_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/set'
volume_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/volume/set'
volume_up_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/volume/up/set'
volume_down_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/volume/down/set'
volume_mute_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/volume/mute/set'
play_sound_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/set'
play_next_sound_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/next/set'
play_previous_sound_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/previous/set'

# define the topics to publish state and information to
light_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/nightlight/state'
brightness_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/nightlight/brightness/state'
rgb_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/nightlight/rgb/state'
sound_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/state'
sound_playlist_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/playlist'
volume_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/volume/state'
play_sound_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/state'
previous_sound_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/previous/state'
next_sound_state_topic = '/'+config.unitTopic+'/'+config.clientId+'/whitenoise/play_sound/next/state'
status_topic = '/'+config.unitTopic+'/'+config.clientId+'/state'

# global variables
global_status = UnitStatus("off",{"r":255,"g":0,"b":200},1,"off","Noise 4",100)
# default sounds dictionary

sound_dictionary = {'Noise 4': '/home/pi/server/sounds/white-noise-4.mp3',
                    'Heater 1': '/home/pi/server/sounds/heater-1.mp3',
                    'Heater 2': '/home/pi/server/sounds/heater-2.mp3',
                    'Motor': '/home/pi/server/sounds/motor.mp3',
                    'Dryer 1': '/home/pi/server/sounds/dryer-1.mp3',
                    'Dryer 2': '/home/pi/server/sounds/dryer-2.mp3',
                    'Fan 1': '/home/pi/server/sounds/fan-1.mp3',
                    'Fan 2': '/home/pi/server/sounds/fan-2.mp3',
                    'Ocean 1': '/home/pi/server/sounds/ocean-1.mp3',
                    'Ocean 2': '/home/pi/server/sounds/ocean-2.mp3',
                    'Ocean 3': '/home/pi/server/sounds/ocean-3.mp3',
                    'Ocean 4': '/home/pi/server/sounds/ocean-4.mp3',
                    'Pink Noise': '/home/pi/server/sounds/pink-noise.mp3', 
                    'Train 1': '/home/pi/server/sounds/train-1.mp3',
                    'Train 2': '/home/pi/server/sounds/train-2.mp3',
                    'Storm': '/home/pi/server/sounds/storm.mp3', 
                    'Stream 1': '/home/pi/server/sounds/stream-1.mp3',
                    'Stream 2': '/home/pi/server/sounds/stream-2.mp3',
                    'Blender 1': '/home/pi/server/sounds/blender-1.mp3',
                    'Blender 2': '/home/pi/server/sounds/blender-2.mp3',
                    'Waves 1': '/home/pi/server/sounds/waves-1.mp3',
                    'Waves 2': '/home/pi/server/sounds/waves-2.mp3',
                    'Rain 1': '/home/pi/server/sounds/rain-1.mp3',
                    'Rain 2': '/home/pi/server/sounds/rain-2.mp3',
                    'Rain 3': '/home/pi/server/sounds/rain-3.mp3',
                    'Rain 4': '/home/pi/server/sounds/rain-4.mp3',
                    'White Noise 1': '/home/pi/server/sounds/white-noise-1.mp3',
                    'White Noise 2': '/home/pi/server/sounds/white-noise-2.mp3',
                    'White Noise 3': '/home/pi/server/sounds/white-noise-3.mp3',
                    'White Noise 4': '/home/pi/server/sounds/white-noise-4.mp3',
                    'White Noise 5': '/home/pi/server/sounds/white-noise-5.mp3',
                    'White Noise 6': '/home/pi/server/sounds/white-noise-6.mp3'}

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
    handle_status()

# The callback for when a PUBLISH message is received from the server.
def on_message_received(client, userdata, msg):
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

def handle_status():
    client.publish(status_topic, json.dumps(global_status), 0, False)

def handle_nightlight_switch_state_request():
    client.publish(light_state_topic, global_status.lightStatus, 0, False)

def handle_nightlight_color_state_request():
    client.publish(rgb_state_topic, json.dumps(global_status.rgbSetting), 0, False)


def handle_nightlight_brightness_state_request():
    client.publish(brightness_state_topic, global_status.rgbBrightness, 0, False)


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


def handle_set_play_next_request():
    keyList = sorted(sound_dictionary.keys())
    for i, v in enumerate(keyList):
        if v == global_status.soundSetting:
            handle_previous_next_state_request(keyList[i], keyList[i+2], keyList[i+1])
            global_status.soundSetting = keyList[i+1]
            stop_sound()
            play_sound(sound_dictionary[global_status.soundSetting])
            change_volume(global_status.volumeSetting)
    handle_whitenoise_sound_state_request()


def handle_set_play_previous_request():
    keyList = sorted(sound_dictionary.keys())
    for i, v in enumerate(keyList):
        if v == global_status.soundSetting:
            handle_previous_next_state_request(keyList[i-2], keyList[i], keyList[i-1])
            global_status.soundSetting = keyList[i-1]
            stop_sound()
            play_sound(sound_dictionary[global_status.soundSetting])
            change_volume(global_status.volumeSetting)
    handle_whitenoise_sound_state_request()


def handle_set_volume_request(payload):
    global_status.volumeSetting = int(Decimal(json.loads(payload)) * 100)
    change_volume(global_status.volumeSetting)
    handle_whitenoise_volume_state_request()


def handle_volume_up_request():
    change_volume((global_status.volumeSetting+5))


def handle_volume_down_request():
    change_volume((global_status.volumeSetting-5))


def handle_volume_mute_request():
    change_volume(0)


def handle_set_play_sound_request(payload):
    val = json.loads(payload)
    sound_name = val["action"]
    stop_sound()
    global_status.soundSetting = sound_name
    play_sound(sound_dictionary[global_status.soundSetting])
    handle_whitenoise_sound_state_request()


def handle_set_sound_request(payload):
    jsonPayload = json.loads(payload)
    if jsonPayload["action"] == 'off':
        stop_sound()
        global_status.soundStatus = "off"
    else:
        stop_sound()
        play_sound(sound_dictionary[global_status.soundSetting])
        global_status.soundStatus = "on"
        change_volume(global_status.volumeSetting)
    handle_whitenoise_switch_state_request()

# -------------------------------------------------------------------------------------------------------------
# Light set section
# -------------------------------------------------------------------------------------------------------------


def handle_set_brightness_request(payload):
    global_status.rgbBrightness = payload
    handle_nightlight_brightness_state_request()


def handle_set_light_request(payload):
    jsonPayload = json.loads(payload)
    if jsonPayload["action"] == 'off':
        nightlight_set(0, 0, 0, 0.5)
        nightlight_on()
        nightlight_off()
        global_status.lightStatus = 'off'
    else:
        nightlight_off()
        nightlight_set(red=global_status.rgbSetting.red, green=global_status.rgbSetting.green,
                       blue=global_status.rgbSetting.blue, brightness=global_status.rgbBrightness)
        nightlight_on()
        global_status.lightStatus = "on"
    handle_nightlight_switch_state_request()


def handle_set_rgb_request(payload):
    jsonPayload = json.loads(payload)
    global_status.rgbSetting.red=jsonPayload["r"]
    global_status.rgbSetting.green=jsonPayload["g"]
    global_status.rgbSetting.blue=jsonPayload["b"],
    handle_nightlight_color_state_request()

# -------------------------------------------------------------------------------------------------------------


client = mqtt.Client(client_id=config.clientId)

#client.tls_set(ca_certs=config.caBundlePath, certfile=config.certFilePath, keyfile=config.keyFilePath)
#client.username_pw_set(config.username, config.password)
client.connect(config.mqttHost, config.mqttPort, config.mqttKeepAlive)

client.on_connect = on_connect
client.on_message = on_message_received

client.loop_forever()
