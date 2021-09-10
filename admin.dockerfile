FROM python:3

RUN mkdir -p /opt/src/admin
WORKDIR /opt/src/admin

COPY applications/admin/adminDecorator.py ./adminDecorator.py
COPY applications/admin/application.py ./application.py
COPY applications/admin/configuration.py ./configuration.py
COPY applications/admin/models.py ./models.py
COPY requirements.txt ./requrements.txt

RUN pip install -r ./requrements.txt

ENTRYPOINT ["python", "./application.py"]
