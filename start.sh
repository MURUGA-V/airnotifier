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

echo "=== Writing install.py ==="
cat > ./install.py << 'INSTALLEOF'
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from constants import VERSION
from os import path
from pymongo.errors import CollectionInvalid
from tornado.options import define, options
from util import *
import logging
import pymongo
import tornado.options

EMAIL = "admin@airnotifier"
DEFAULTPASSWORD = "admin"

define("masterdb", default="airnotifier", help="MongoDB DB to store information")
define("mongouri", default="mongodb://localhost:27017/", help="MongoDB host name")
define("apns", default=(), help="APNs address and port")
define("pemdir", default="pemdir", help="Directory to store pems")
define("passwordsalt", default="d2o0n1g2s0h3e1n1g", help="Being used to make password hash")

if __name__ == "__main__":
    if not path.exists("config.py"):
        raise Exception("Please create config.py before running install.py")

    tornado.options.parse_config_file("config.py")
    tornado.options.parse_command_line()
    mongodb = pymongo.MongoClient(options.mongouri)
    masterdb = mongodb[options.masterdb]

    collection_names = masterdb.list_collection_names()

    try:
        if "applications" not in collection_names:
            masterdb.create_collection("applications")
            logging.info("db.applications installed")
    except CollectionInvalid as ex:
        logging.info(("Failed to created applications collection", ex))

    try:
        if "managers" not in collection_names:
            masterdb.create_collection("managers")
            masterdb.managers.create_index("email", unique=True)
            logging.info("db.managers installed")
            try:
                user = masterdb.managers.find_one({"email": EMAIL})
                if not user:
                    manager = {}
                    manager["email"] = EMAIL
                    manager["password"] = get_password(DEFAULTPASSWORD, options.passwordsalt)
                    manager["orgid"] = 0
                    masterdb["managers"].insert_one(manager)
                    logging.info("Admin user created, username: %s, password: %s" % (EMAIL, DEFAULTPASSWORD))
            except Exception as ex:
                logging.error(("Failed to create admin user", ex))
    except CollectionInvalid:
        logging.info("Failed to created managers collection")

    try:
        if "options" not in collection_names:
            masterdb.create_collection("options")
            logging.info("db.options installed")
            try:
                version = masterdb["options"].find_one({"name": "version"})
                if not version:
                    option_ver = {"name": "version", "value": VERSION}
                    masterdb["options"].insert_one(option_ver)
                    logging.info("Version number written: %s" % VERSION)
            except Exception:
                logging.error("Failed to write version number")
    except CollectionInvalid:
        logging.error("db.options installed")
INSTALLEOF

echo "=== Checking logging.ini ==="
if [ ! -f "./logging.ini" ]; then
  cp logging.ini-sample logging.ini
fi

mkdir -p $LOGDIR

echo "=== Running install.py ==="
# Use || true so install failures don't stop the app (collections may already exist)
pipenv run python install.py 2>&1 || true

echo "=== Starting AirNotifier on port ${PORT:-10000} ==="
pipenv run python app.py --port=${PORT:-10000}