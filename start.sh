#!/bin/sh

export LOGDIR=/var/log/airnotifier

echo "=== Current directory ==="
pwd

echo "=== Files in current directory ==="
ls -la

echo "=== Checking config.py ==="
if [ ! -f "./config.py" ]; then
  echo "config.py not found, copying sample..."
  cp config.py-sample config.py
else
  echo "config.py found!"
fi

echo "=== config.py contents ==="
cat ./config.py

echo "=== Checking logging.ini ==="
if [ ! -f "./logging.ini" ]; then
  cp logging.ini-sample logging.ini
fi

mkdir -p $LOGDIR

echo "=== Running install.py ==="
pipenv run python install.py 2>&1
INSTALL_EXIT=$?
echo "=== install.py exited with: $INSTALL_EXIT ==="
if [ $INSTALL_EXIT -ne 0 ]; then
  exit 1
fi

echo "=== Starting AirNotifier on port ${PORT:-10000} ==="
pipenv run python app.py --port=${PORT:-10000}