#!/usr/bin/env python

import logging
import os
import re
import signal
import subprocess
import sys
import time
from queue import Queue, SimpleQueue

from ha_mqtt_discoverable import DeviceInfo, Settings
from ha_mqtt_discoverable.sensors import (
    Button,
    ButtonInfo,
    Number,
    NumberInfo,
    Switch,
    SwitchInfo
)

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


VOLUME_PATTERN = re.compile(b'.+\[(\d+)%', re.DOTALL)
def get_current_volume_percentage() -> int:
    proc = subprocess.run(["amixer", "-M"], capture_output=True, check=True)
    return int(re.match(VOLUME_PATTERN, proc.stdout).group(1))

def set_current_volume_percentage(value: int):
    subprocess.run(["amixer", "-M", "sset", "PCM", f"{value}%"])

def volume_change_request(client, user_data, message):
    payload = int(message.payload.decode())
    set_current_volume_percentage(payload)
    volume_slider.set_value(payload)


volume_slider_info = NumberInfo(
    name=f"{device_name} Volume",
    unique_id="{device_name}_volume",
    mode="box",
    min=0,
    max=100,
    step=1,
    device=device_info
)
volume_slider_settings = Settings(
    mqtt=mqtt_settings,
    entity=volume_slider_info
)
volume_slider = Number(volume_slider_settings, volume_change_request)
volume_slider.set_value(get_current_volume_percentage())

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
