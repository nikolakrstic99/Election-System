FROM python:3

RUN mkdir -p /opt/src/zvanicnik
WORKDIR /opt/src/zvanicnik

COPY applications/admin/adminDecorator.py ./applications/admin/adminDecorator.py
COPY applications/zvanicnik/zvanicnik.py ./application.py
COPY applications/zvanicnik/configuration.py ./configuration.py
COPY applications/models.py ./applications/models.py
COPY requirements.txt ./requrements.txt
COPY applications/zvanicnik/votes.csv ./votes.csv
RUN pip install -r ./requrements.txt

ENTRYPOINT ["python", "./application.py"]
