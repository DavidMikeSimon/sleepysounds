#!/usr/bin/env python

import os
import time

from ha_mqtt_discoverable import DeviceInfo, Settings
from ha_mqtt_discoverable.sensors import Button, ButtonInfo, Switch, SwitchInfo
from just_playback import Playback

import config

device_name = f"{config.name_prefix} Sleepy Sounds"

device_info = DeviceInfo(
    name=device_name,
    identifiers=device_name
)

mqtt_settings = Settings.MQTT(host=config.mqtt_host, username=config.username, password=config.password)

def switch_change_request(client, user_data, message):
    payload = message.payload.decode()
    if payload == "ON":
        playing_switch.on()
        playback.play()
    elif payload == "OFF":
        playing_switch.off()
        playback.stop()
    else:
        print(f"Unknown payload {payload}")

playing_switch_info = SwitchInfo(
    name=f"{device_name} Playing",
    unique_id="{device_name}_playing",
    device=device_info
)
playing_switch_settings = Settings(mqtt=mqtt_settings, entity=playing_switch_info)
playing_switch = Switch(playing_switch_settings, switch_change_request)

playing_switch.off()

def next_button_request(client, user_data, message):
    payload = message.payload.decode()
    print(f"Got next button request {payload}")

next_button_info = ButtonInfo(
    name=f"{device_name} Next Sound",
    unique_id="{device_name}_playing",
    device=device_info
)
next_button_settings = Settings(mqtt=mqtt_settings, entity=next_button_info)
next_button = Button(next_button_settings, next_button_request)

# FIXME: This should happen automatically
next_button.write_config()

playback = Playback()
playback.loop_at_end(True)

sound_dictionary = { os.path.splitext(fn)[0]: fn for fn in os.listdir(config.sounds_dir) }

def main():
    playback.load_file(os.path.join(config.sounds_dir, list(sound_dictionary.values())[0]))
    #  playback.play()

    while True:
        time.sleep(2)
        #  print(f"{playback.curr_pos} of {playback.duration}")

if __name__ == "__main__":
    main()
