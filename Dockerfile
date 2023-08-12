FROM python:3

RUN apt update && apt install -y alsa-utils && apt clean

COPY app /usr/src/app

WORKDIR /usr/src/app

RUN pip install --no-cache-dir -r ./requirements.txt

CMD [ "python", "./sleepysounds.py" ]
