from api.tokens import TokenV2Handler
from tornado.testing import AsyncHTTPTestCase
from container import Container
import tornado.web

from tornado.options import define

def make_app():
    # mimic the simple container used in test_push
    class CollectionAPI:
        def __init__(self):
            self.stored = []

        def find_one(self, query):
            # return a dummy key with all permissions
            return {"permission": 0b11111}

        def insert(self, doc):
            self.stored.append(doc)

        def update_one(self, query, update, upsert=False):
            # simulate upsert behaviour by appending if not found
            token = query.get("token")
            existing = [d for d in self.stored if d.get("token") == token]
            if existing:
                existing[0].update(update.get("$set", {}))
                return type("r", (), {"matched_count": 1, "upserted_id": None})
            else:
                new = update.get("$set", {})
                self.stored.append(new)
                return type("r", (), {"matched_count": 0, "upserted_id": 1})

    class MockMongo:
        def __init__(self):
            self.tokens = CollectionAPI()
            self.keys = CollectionAPI()
            self.logs = CollectionAPI()

    class WebApplication(tornado.web.Application):
        def __init__(self, handlers, container):
            self.container = container
            self.mongodb = {"myapp": MockMongo()}
            super(WebApplication, self).__init__(handlers)

    class Dao:
        def __init__(self, mongodb, appoptions):
            self.mongodb = mongodb
            self.masterdb = None
            self.options = appoptions

        def set_current_app(self, name):
            pass

        def get_version(self):
            return "2.0.0"

        def find_app_by_name(self, name):
            return {"name": name, "shortname": name}

        def update_app_by_name(self, name):
            pass

        def find_token(self, token):
            # always return None so that handler goes through "not found" path
            return None

        def add_token(self, token):
            # not used by TokenV2Handler
            pass

    data = (
        ("mongodburi", ".........", None),
        ("mongodbconn", "....", None),
        ("services", "...", None),
        ("serveroptions", "xxxx", None),
        ("dao", Dao, ("mongodbconn", "serveroptions")),
    )
    container = Container(data)
    return WebApplication([(r"/api/v2/tokens", TokenV2Handler)], container)

headers = {
    "X-AN-APP-NAME": "myapp",
    "X-AN-APP-KEY": "xxxx",
}

class TestTokenAPI(AsyncHTTPTestCase):
    def get_app(self):
        return make_app()

    def test_create_token_success(self):
        body = '{"token":"abcdef","device":"fcm"}'
        response = self.fetch("/api/v2/tokens", method="POST", body=body, headers=headers)
        self.assertEqual(response.code, 200)

    def test_create_token_invalid_ios(self):
        body = '{"token":"short","device":"ios"}'
        response = self.fetch("/api/v2/tokens", method="POST", body=body, headers=headers)
        self.assertEqual(response.code, 400)

if __name__ == "__main__":
    import unittest

    unittest.main()
