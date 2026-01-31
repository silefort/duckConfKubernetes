FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y openssh-server curl && \
    rm -rf /var/lib/apt/lists/*

# Installation Docker CLI (fonctionne avec le socket Podman)
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-24.0.7.tgz | \
    tar xz --strip-components=1 -C /usr/local/bin docker/docker

# Configuration SSH
RUN mkdir -p /var/run/sshd && \
    echo 'root:root' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Dependances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
