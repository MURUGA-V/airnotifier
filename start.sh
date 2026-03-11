#!/bin/sh
set -e

export LOGDIR=/var/log/airnotifier

if [ ! -f "./config.py" ]; then
  cp config.py-sample config.py
fi

sed -i 's/https = True/https = False/g' ./config.py

if [ ! -f "./logging.ini" ]; then
  cp logging.ini-sample logging.ini
fi

mkdir -p $LOGDIR

echo "Installing AirNotifier ..."
pipenv run python install.py

echo "Starting AirNotifier on port ${PORT:-10000} ..."
pipenv run python app.py --port=${PORT:-10000}