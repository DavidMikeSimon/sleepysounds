import os

soundsDir = os.environ['SOUNDS_DIR']

clientId = os.environ['CLIENT_ID']

mqttHost = os.environ['MQTT_HOST']
mqttKeepAlive = 120
mqttPort = 8883
unitTopic = os.environ['UNIT_TOPIC']

username = os.environ['MQTT_USER']
password = os.environ['MQTT_PASS']
