FROM tensorflow/tensorflow:latest-gpu

USER root
ENV PYTHONPATH=/app/backend

COPY ./src /app/backend
COPY ./keras /root/.keras
COPY ./config /config

RUN pip install --no-cache-dir \
        Pillow==7.1.1 \
        boto3==1.14.44

RUN chmod +x /config/entrypoint.sh
                    
WORKDIR /app/backend
ENTRYPOINT ["/config/entrypoint.sh"]

