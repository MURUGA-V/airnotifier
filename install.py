#!/usr/bin/env python
# -*- coding: utf-8 -*-

from constants import VERSION
from hashlib import sha1
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
define(
    "passwordsalt", default="d2o0n1g2s0h3e1n1g", help="Being used to make password hash"
)


if __name__ == "__main__":
    if not path.exists("config.py"):
        raise Exception("Please create config.py before running install.py")

    tornado.options.parse_config_file("config.py")
    tornado.options.parse_command_line()
    mongodb = pymongo.MongoClient(options.mongouri)
    masterdb = mongodb[options.masterdb]

    # Fixed: use list_collection_names() instead of removed collection_names()
    collection_names = masterdb.list_collection_names()

    try:
        if "applications" not in collection_names:
            masterdb.create_collection("applications")
            logging.info("db.applications installed")
    except CollectionInvalid as ex:
        logging.info(("Failed to created applications collection", ex))
        pass

    try:
        if "managers" not in collection_names:
            masterdb.create_collection("managers")
            # Fixed: use create_index() instead of removed ensure_index()
            masterdb.managers.create_index("email", unique=True)
            logging.info("db.managers installed")
            try:
                user = masterdb.managers.find_one({"email": EMAIL})
                if not user:
                    manager = {}
                    manager["email"] = EMAIL
                    manager["password"] = get_password(
                        DEFAULTPASSWORD, options.passwordsalt
                    )
                    manager["orgid"] = 0
                    # Fixed: use insert_one() instead of removed insert()
                    masterdb["managers"].insert_one(manager)
                    logging.info(
                        "Admin user created, username: %s, password: %s"
                        % (EMAIL, DEFAULTPASSWORD)
                    )
            except Exception as ex:
                logging.error(("Failed to create admin user", ex))

    except CollectionInvalid:
        logging.info("Failed to created managers collection")
        pass

    try:
        if "options" not in collection_names:
            masterdb.create_collection("options")
            logging.info("db.options installed")
            try:
                version = masterdb["options"].find_one({"name": "version"})
                if not version:
                    option_ver = {}
                    option_ver["name"] = "version"
                    option_ver["value"] = VERSION
                    # Fixed: use insert_one() instead of removed insert()
                    masterdb["options"].insert_one(option_ver)
                    logging.info(("Version number written: %s" % VERSION))
            except Exception:
                logging.error("Failed to write version number")
    except CollectionInvalid:
        logging.error("db.options installed")