FROM python:3-alpine

ADD requirements.txt /tmp/requirements.txt

RUN python -m pip install --upgrade pip
RUN pip install -r /tmp/requirements.txt

COPY getter.py /app/

WORKDIR /app

CMD ["python", "/app/getter.py"]
