#!/bin/sh

export LOGDIR=/var/log/airnotifier

echo "=== Step 1: Checking config.py ==="
if [ ! -f "./config.py" ]; then
  echo "config.py not found, copying sample..."
  cp config.py-sample config.py
else
  echo "config.py found!"
fi

echo "=== Step 2: config.py contents ==="
cat ./config.py

echo "=== Step 3: Checking logging.ini ==="
if [ ! -f "./logging.ini" ]; then
  cp logging.ini-sample logging.ini
fi

mkdir -p $LOGDIR

echo "=== Step 4: Running install.py ==="
pipenv run python install.py 2>&1
INSTALL_EXIT=$?
echo "=== install.py exited with status: $INSTALL_EXIT ==="

if [ $INSTALL_EXIT -ne 0 ]; then
  echo "=== INSTALL FAILED ==="
  exit 1
fi

echo "=== Step 5: Starting AirNotifier on port ${PORT:-10000} ==="
pipenv run python app.py --port=${PORT:-10000}