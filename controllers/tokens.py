#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012, Dongsheng Cai
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the Dongsheng Cai nor the names of its
#      contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL DONGSHENG CAI BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import tornado.web
import logging
import time

from controllers.base import *


@route(r"/applications/([^/]+)/tokens[\/]?")
class AppTokensHandler(WebBaseHandler):
    @tornado.web.authenticated
    def get(self, appname):
        self.appname = appname
        app = self.masterdb.applications.find_one({"shortname": appname})
        if not app:
            raise tornado.web.HTTPError(500)
        page = self.get_argument("page", None)
        perpage = 50

        token_id = self.get_argument("delete", None)
        if token_id:
            self.db.tokens.delete_one({"_id": ObjectId(token_id)})
            self.redirect("/applications/%s/tokens" % appname)
            return
        if page:
            tokens = (
                self.db.tokens.find()
                .sort("created", DESCENDING)
                .skip(int(page) * perpage)
                .limit(perpage)
            )
        else:
            page = 0
            tokens = self.db.tokens.find().sort("created", DESCENDING).limit(perpage)
        self.render("app_tokens.html", app=app, tokens=tokens, page=int(page))

    @tornado.web.authenticated
    def post(self, appname):
        self.appname = appname
        app = self.masterdb.applications.find_one({"shortname": appname})
        if not app:
            raise tornado.web.HTTPError(500)

        # allow an administrator to manually register a token; parameters are
        # intentionally the same as the REST API so that scripts and forms can
        # share code
        device = self.get_argument("device", DEVICE_TYPE_FCM).lower()
        token_value = self.get_argument("token", "").strip()
        channel = self.get_argument("channel", "default")

        if not token_value:
            # nothing supplied
            self.redirect(f"/applications/{appname}/tokens")
            return

        # basic validation for ios tokens
        if device == DEVICE_TYPE_IOS and len(token_value) != 64:
            self.redirect(f"/applications/{appname}/tokens")
            return

        try:
            self.db.tokens.update_one(
                {"device": device, "token": token_value, "appname": appname},
                {"$set": {
                    "device": device,
                    "token": token_value,
                    "appname": appname,
                    "channel": channel,
                    "created": int(time.time()),
                }},
                upsert=True,
            )
        except Exception:
            logging.exception("unable to upsert token from web UI")

        self.redirect(f"/applications/{appname}/tokens")