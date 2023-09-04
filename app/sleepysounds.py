#!/usr/bin/env python

import logging
import os
import signal
import sys
import time
from queue import Queue, SimpleQueue

from ha_mqtt_discoverable import DeviceInfo, Settings
from ha_mqtt_discoverable.sensors import Button, ButtonInfo, Switch, SwitchInfo

import config
from playback import (
    PlaybackThread,
    PlaybackCommand,
    StartCommand,
    StopCommand,
    QuitCommand,
    PlaybackStatusMessage,
    PlaybackStartingMessage,
    PlaybackStoppingMessage,
    PlaybackStoppingMessage,
    PlaybackThreadEndedMessage,
)

sound_dictionary = {os.path.splitext(fn)[0]: fn for fn in os.listdir(config.sounds_dir)}
sound_dictionary_keys = sorted(list(sound_dictionary.keys()))
sound_dictionary_index = 0

device_name = f"{config.name_prefix} Sleepy Sounds"

device_info = DeviceInfo(name=device_name, identifiers=device_name)

mqtt_settings = Settings.MQTT(
    host=config.mqtt_host, username=config.username, password=config.password
)

playback_command_queue: Queue[PlaybackCommand] = Queue()
playback_status_queue: SimpleQueue[PlaybackStatusMessage] = SimpleQueue()
playback_thread = PlaybackThread(
    command_queue=playback_command_queue,
    status_queue=playback_status_queue
)

def get_current_sound_path() -> str:
    fn = sound_dictionary[sound_dictionary_keys[sound_dictionary_index]]
    return os.path.join(config.sounds_dir, fn)


def switch_change_request(client, user_data, message):
    payload = message.payload.decode()
    if payload == "ON":
        playback_command_queue.put(StartCommand(path=get_current_sound_path()))
    elif payload == "OFF":
        playback_command_queue.put(StopCommand())
    else:
        logging.error(f"Unknown payload {payload} in switch_change_request")


playing_switch_info = SwitchInfo(
    name=f"{device_name} Playing",
    unique_id="{device_name}_playing",
    device=device_info
)
playing_switch_settings = Settings(
    mqtt=mqtt_settings,
    entity=playing_switch_info
)
playing_switch = Switch(playing_switch_settings, switch_change_request)

# Have to set the switch state to make ha_mqtt_discoverable publish the
# discovery message.
playing_switch.off()


def next_button_request(client, user_data, message):
    playback_command_queue.put(StopCommand())
    global sound_dictionary_index
    sound_dictionary_index = (sound_dictionary_index + 1) % len(sound_dictionary_keys)
    playback_command_queue.put(StartCommand(path=get_current_sound_path()))


next_button_info = ButtonInfo(
    name=f"{device_name} Next Sound",
    unique_id="{device_name}_playing",
    device=device_info,
)
next_button_settings = Settings(mqtt=mqtt_settings, entity=next_button_info)
next_button = Button(next_button_settings, next_button_request)

# FIXME: This should happen automatically
next_button.write_config()

received_terminate_signal = False
def handle_terminate_signal(signum, frame):
    global received_terminate_signal
    if received_terminate_signal:
        logging.warning(f"Received second terminate signal {signum}, quitting hard")
        sys.exit(1)

    logging.info(f"Received terminate signal {signum}")
    received_terminate_signal = True
    playback_command_queue.put(QuitCommand())


def main():
    playback_thread.start()
    signal.signal(signal.SIGINT, handle_terminate_signal)
    signal.signal(signal.SIGTERM, handle_terminate_signal)

    while True:
        status_message = playback_status_queue.get()
        match status_message:
            case PlaybackStartingMessage(path):
                logging.info(f"Playback starting: {path}")
                playing_switch.on()
            case PlaybackStoppingMessage():
                logging.info("Playback stopping")
                playing_switch.off()
            case PlaybackThreadEndedMessage():
                logging.info("Playback thread ended")
                return



if __name__ == "__main__":
    main()
