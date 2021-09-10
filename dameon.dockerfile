FROM python:3

RUN mkdir -p /opt/src/dameon
WORKDIR /opt/src/dameon

COPY dameon.py ./dameon.py
COPY configuration.py ./configuration.py
COPY applications/models.py ./applications/models.py
COPY requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./dameon.py"]
