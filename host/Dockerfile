FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    iputils-ping \
    net-tools \
    inetutils-traceroute \
    iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY host.py .

RUN mkdir -p /app/logs && chmod 777 /app/logs

CMD ["python", "host.py"]
