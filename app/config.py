import os

name_prefix = os.environ.get('NAME_PREFIX', os.uname().nodename)
sounds_dir = os.environ.get('SOUNDS_DIR', '/sounds')

mqtt_host = os.environ.get('MQTT_HOST', 'localhost')
username = os.environ.get('MQTT_USER', '')
password = os.environ.get('MQTT_PASS', '')

alsa_control = os.environ.get('ALSA_CONTROL', 'PCM')
