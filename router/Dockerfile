FROM python:3.11-slim

WORKDIR /app

# Instalar o pacote necessário para usar o ping
RUN apt-get update && apt-get install -y iproute2 iputils-ping traceroute procps


COPY router.py .

RUN mkdir -p /app/logs

CMD ["python", "router.py"]
