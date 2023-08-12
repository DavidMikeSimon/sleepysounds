FROM python:3

COPY app /usr/src/app

WORKDIR /usr/src/app

RUN pip install --no-cache-dir -r ./requirements.txt

CMD [ "python", "./sleepysounds.py" ]
