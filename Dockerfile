FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y python3 python3-pip curl unzip && \
    pip3 install --no-cache-dir awscli && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /data
