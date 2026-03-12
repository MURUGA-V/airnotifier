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

from http.client import BAD_REQUEST, FORBIDDEN, NOT_FOUND, INTERNAL_SERVER_ERROR, OK
from routes import route
from api import APIBaseHandler, EntityBuilder
from constants import DEVICE_TYPE_IOS, DEVICE_TYPE_FCM
import binascii
import logging
from util import json_decode


@route(r"/api/v2/tokens/([^/]+)")
class TokenV2HandlerGet(APIBaseHandler):
    def delete(self, token):
        """Delete a token
        """
        # To check the access key permissions we use bitmask method.
        if not self.can("delete_token"):
            self.send_response(FORBIDDEN, dict(error="No permission to delete token"))
            return

        try:
            result = self.db.tokens.delete_one({"token": token})
            if result.deleted_count == 0:
                self.send_response(NOT_FOUND, dict(status="Token does't exist"))
            else:
                self.send_response(OK, dict(status="deleted"))
        except Exception as ex:
            self.send_response(INTERNAL_SERVER_ERROR, dict(error=str(ex)))


@route(r"/api/v2/tokens[\/]?")
class TokenV2Handler(APIBaseHandler):
    def post(self):
        """Create a new token
        """
        if not self.can("create_token"):
            self.send_response(FORBIDDEN, dict(error="No permission to create token"))
            return

        data = json_decode(self.request.body)

        device = data.get("device", DEVICE_TYPE_FCM).lower()
        channel = data.get("channel", "default")
        devicetoken = data.get("token", "")

        if device == DEVICE_TYPE_IOS:
            if len(devicetoken) != 64:
                self.send_response(BAD_REQUEST, dict(error="Invalid token"))
                return
            try:
                binascii.unhexlify(devicetoken)
            except Exception as ex:
                # token string is not valid hex; reject immediately and don't fall
                # through to the upsert below
                self.send_response(BAD_REQUEST, dict(error="Invalid token"))
                return

        token = EntityBuilder.build_token(devicetoken, device, self.appname, channel)
        try:
            # use update_one to avoid pymongo deprecation warnings and make intent
            # clearer (single document upsert)
            result = self.db.tokens.update_one(
                {"device": device, "token": devicetoken, "appname": self.appname},
                {"$set": token},
                upsert=True,
            )
            # update_one result has matched_count and upserted_id
            if result.matched_count:
                # an existing document was updated
                self.add_to_log("Token exists", devicetoken)
                self.send_response(OK)
            else:
                # document inserted
                self.add_to_log("Add token", devicetoken)
                self.send_response(OK)
        except Exception as ex:
            self.send_response(INTERNAL_SERVER_ERROR, dict(error=str(ex)))