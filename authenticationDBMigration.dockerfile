FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication



COPY authentication/migrate.py ./migrate.py
COPY authentication/configuration.py ./configuration.py
COPY authentication/models.py ./models.py
COPY authentication/requrements.txt ./requrements.txt
RUN pip install -r ./requrements.txt

ENTRYPOINT ["python", "./migrate.py"]
