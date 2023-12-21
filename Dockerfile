FROM python:3.9-slim-buster
LABEL maintainer="lapy@lapy.link"

ENV NTFY_BASE="ntfy.sh" \
    NTFY_TOPIC="ChangeHere-09815a15-18d0-436f-8403-df5ac7be3f23" \
    USB_PID="0x1fc9" \
    USB_GID="0x2016"

COPY . /app/server

WORKDIR /app/server

RUN pip3 install -r requirements.txt
RUN python setup.py install

ENTRYPOINT ["python", "stream_ntfy.py"]