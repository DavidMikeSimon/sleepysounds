#!/usr/bin/env python

import os
import signal
import sys
import time
from queue import Queue

from ha_mqtt_discoverable import DeviceInfo, Settings
from ha_mqtt_discoverable.sensors import Button, ButtonInfo, Switch, SwitchInfo

import config
from playback import PlaybackCommand, StartCommand, StopCommand, QuitCommand, PlaybackThread

sound_dictionary = {os.path.splitext(fn)[0]: fn for fn in os.listdir(config.sounds_dir)}
sound_dictionary_keys = sorted(list(sound_dictionary.keys()))
sound_dictionary_index = 0

device_name = f"{config.name_prefix} Sleepy Sounds"

device_info = DeviceInfo(name=device_name, identifiers=device_name)

mqtt_settings = Settings.MQTT(
    host=config.mqtt_host, username=config.username, password=config.password
)

playback_command_queue: Queue[PlaybackCommand] = Queue()
playback_thread = PlaybackThread(playback_command_queue)

def get_current_sound_path() -> str:
    fn = sound_dictionary[sound_dictionary_keys[sound_dictionary_index]]
    return os.path.join(config.sounds_dir, fn)


def switch_change_request(client, user_data, message):
    payload = message.payload.decode()
    if payload == "ON":
        playback_command_queue.put(StartCommand(path=get_current_sound_path()))
        playing_switch.on()
    elif payload == "OFF":
        playback_command_queue.put(StopCommand())
        playing_switch.off()
    else:
        print(f"Unknown payload {payload} in switch_change_request")


playing_switch_info = SwitchInfo(
    name=f"{device_name} Playing", unique_id="{device_name}_playing", device=device_info
)
playing_switch_settings = Settings(mqtt=mqtt_settings, entity=playing_switch_info)
playing_switch = Switch(playing_switch_settings, switch_change_request)

playing_switch.off()


def next_button_request(client, user_data, message):
    playback_command_queue.put(StopCommand())
    global sound_dictionary_index
    sound_dictionary_index = (sound_dictionary_index + 1) % len(sound_dictionary_keys)
    playback_command_queue.put(StartCommand(path=get_current_sound_path()))
    playing_switch.on()


next_button_info = ButtonInfo(
    name=f"{device_name} Next Sound",
    unique_id="{device_name}_playing",
    device=device_info,
)
next_button_settings = Settings(mqtt=mqtt_settings, entity=next_button_info)
next_button = Button(next_button_settings, next_button_request)

# FIXME: This should happen automatically
next_button.write_config()

def handle_interrupt(signum, frame):
    print("Received SIGINT, exiting")
    playback_command_queue.put(QuitCommand())
    playback_thread.join()
    sys.exit(0)


def main():
    playback_thread.start()
    signal.signal(signal.SIGINT, handle_interrupt)

    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
