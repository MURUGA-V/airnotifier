#!/bin/sh

export LOGDIR=/var/log/airnotifier

echo "=== Step 1: Checking config.py ==="
ls -la ./config.py 2>&1 || echo "config.py NOT found"
cat ./config.py

echo "=== Step 2: Checking logging.ini ==="
if [ ! -f "./logging.ini" ]; then
  cp logging.ini-sample logging.ini
fi

mkdir -p $LOGDIR

echo "=== Step 3: Running install.py ==="
pipenv run python install.py 2>&1
INSTALL_EXIT=$?
echo "=== install.py exited with: $INSTALL_EXIT ==="
if [ $INSTALL_EXIT -ne 0 ]; then
  exit 1
fi

echo "=== Step 4: Starting AirNotifier on port ${PORT:-10000} ==="
pipenv run python app.py --port=${PORT:-10000}