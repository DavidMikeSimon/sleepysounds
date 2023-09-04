FROM python:3.11.5

RUN apt update && apt install -y alsa-utils && apt clean

COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY app /usr/src/app

WORKDIR /usr/src/app

CMD [ "python", "-u", "./sleepysounds.py" ]
