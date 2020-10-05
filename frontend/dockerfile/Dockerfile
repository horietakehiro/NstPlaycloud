FROM python:3.6-slim

ENV PYTHONPATH /app
COPY ./src /app/frontend
COPY ./config /config

EXPOSE 80
EXPOSE 443

RUN apt update \
    && apt install -y `cat /config/apt.txt` \
    && apt clean

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -fr awscliv2*

RUN pip install --no-cache-dir -r /config/requirements.txt

RUN chmod +x /config/entrypoint.sh

COPY ./config/aws /root/.aws
WORKDIR /app/frontend
ENTRYPOINT ["/config/entrypoint.sh"]
