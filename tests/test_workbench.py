import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import audit_workbench
import server


class QuietHandler(server.Handler):
    def log_message(self, *_):
        pass


class WorkbenchTests(unittest.TestCase):
    def test_artifact_contract(self):
        self.assertEqual(audit_workbench.audit()["status"], "PASS")

    def test_api_and_database_migration_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            original_db = server.DB
            test_db = Path(temp) / "test.sqlite3"
            server.DB = test_db
            httpd = None
            thread = None
            try:
                server.init()
                httpd = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
                thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{httpd.server_port}"

                native = self.get_json(base + "/api/native")
                self.assertEqual(native["protocol"]["status"], native["exposure"]["classification"])
                geometry = self.get_json(base + "/geometry/compiled.json")
                feature = geometry["profiles"]["huet"]["canonical_face_ids"][0]

                code, _ = self.request(base + "/workbench.sqlite3", expected_error=True)
                self.assertEqual(code, 404)
                code, _ = self.request(base + "/workbench.sqlite3", method="HEAD", expected_error=True)
                self.assertEqual(code, 404)
                code, body = self.post_json(base + "/api/placements", [])
                self.assertEqual((code, body["error"]), (400, "JSON object required"))

                unsupported = {"overlay":"trial-a","profile":"huet","feature":feature,"entity":"Unsupported","role":"candidate","status":"source-backed"}
                code, body = self.post_json(base + "/api/placements", unsupported)
                self.assertEqual((code, body["error"]), (400, "Source-backed placements require a source or passage"))

                placement = {"overlay":"trial-a","profile":"huet","feature":feature,"entity":"Test entity","tradition":"test","role":"candidate","status":"exploratory"}
                code, _ = self.post_json(base + "/api/placements", placement)
                self.assertEqual(code, 201)
                event = {"overlay":"trial-a","profile":"huet","feature":feature,"inputs":["A","B"],"result":"C","tradition":"test"}
                code, _ = self.post_json(base + "/api/events", event)
                self.assertEqual(code, 201)

                state = self.get_json(base + "/api/state")
                self.assertEqual(len(state["placements"]), 1)
                self.assertEqual(len(state["relation_events"]), 1)
                self.assertEqual(state["relation_events"][0]["profile"], "huet")
                self.assertEqual(len(state["event_participants"]), 3)
            finally:
                if httpd:
                    httpd.shutdown()
                    httpd.server_close()
                if thread:
                    thread.join(timeout=5)
                    self.assertFalse(thread.is_alive(), "HTTP test server did not stop")
                server.DB = original_db
                # This is deliberately stronger than relying on
                # TemporaryDirectory cleanup. Windows rejects this unlink if
                # any request handler leaked a SQLite connection.
                if test_db.exists():
                    test_db.unlink()

    @staticmethod
    def request(url, data=None, headers=None, method=None, expected_error=False):
        request = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            if not expected_error and error.code >= 500:
                raise
            return error.code, error.read()

    @classmethod
    def get_json(cls, url):
        code, body = cls.request(url)
        if code != 200:
            raise AssertionError((code, body))
        return json.loads(body)

    @classmethod
    def post_json(cls, url, value):
        code, body = cls.request(url, json.dumps(value).encode(), {"Content-Type":"application/json"}, "POST", True)
        return code, json.loads(body)


if __name__ == "__main__":
    unittest.main()
