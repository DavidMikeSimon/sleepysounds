FROM python:3

RUN apt update && apt install -y alsa-utils && apt clean

RUN pip install --no-cache-dir -r ./requirements.txt

COPY app /usr/src/app

WORKDIR /usr/src/app

CMD [ "python", "./sleepysounds.py" ]
