# To run:
# docker run -d --restart unless-stopped --net=host --name MQTTBabyNightLightWhitenoiseMaker-container MQTTBNAM

FROM python:3
MAINTAINER Keith Berry "keithwberry@gmail.com"

WORKDIR /usr/src/app

# Change url below to the proper url 
ADD https://github.com/[username]/[path to release].tar.gz .
RUN gunzip -c master.tar.gz | tar xvf -

# change dirname below to proper dirname
WORKDIR /usr/src/app/mqtt_bnam-master

RUN pip install --no-cache-dir -r ./requirements.txt

CMD [ "python", "./mqtt_bnam.py" ]
