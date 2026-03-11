#!/bin/sh

export LOGDIR=/var/log/airnotifier

echo "=== Writing config.py ==="
cat > ./config.py << 'CONFIGEOF'
port = 10000
mongouri = "mongodb+srv://muruga:12345@cluster0.jdcepmv.mongodb.net/?appName=Cluster0"
passwordsalt = 'd2o0n1g2s0h3e1n1g'
cookiesecret = 'airnotifiercookiesecret'
debug = False
masterdb = "airnotifier"
collectionprefix = "obj_"
dbprefix = ""
appprefix = "app_"
CONFIGEOF

echo "=== config.py written ==="
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