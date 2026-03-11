FROM python:3.8

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive TERM=linux

EXPOSE 10000

RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates

RUN pip3 install pipenv

RUN mkdir -p /airnotifier && \
    mkdir -p /var/airnotifier/pemdir && \
    mkdir -p /var/log/airnotifier

WORKDIR /airnotifier

# Copy your repo files directly instead of cloning upstream
COPY . /airnotifier/

RUN pipenv install --skip-lock

RUN chmod +x /airnotifier/start.sh

VOLUME ["/var/log/airnotifier", "/var/airnotifier/pemdir"]

ENTRYPOINT ["/airnotifier/start.sh"]