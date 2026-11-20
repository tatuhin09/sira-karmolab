"""Offline HTTP integration tests: no credentials and no model requests."""
import json
import sys
import tempfile
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assessment import assess
from run import Handler
from store import Store

class QuietHandler(Handler):
    def log_message(self, *args):
        pass

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / 'practice.sqlite3')
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, store=self.store))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.addCleanup(self.close_server)
        with urlopen(self.base + '/api/policy') as response:
            self.cookie = response.headers['Set-Cookie'].split(';')[0]

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def call(self, path, payload=None, cookie=None, origin=None):
        headers = {'Cookie': self.cookie if cookie is None else cookie}
        if origin:
            headers['Origin'] = origin
        body = None
        if payload is not None:
            body = json.dumps(payload).encode()
            headers['Content-Type'] = 'application/json'
        with urlopen(Request(self.base + path, data=body, headers=headers)) as response:
            return json.load(response)

    def test_retries_do_not_repeat_assessment_and_conflicts_reject(self):
        payload = {'id': str(uuid4()), 'case_id': 'initial', 'answer': 'Could you send an order number and photo?'}
        with patch('run.review', side_effect=lambda a,c,b: assess(a,c)) as model:
            first = self.call('/api/assess', payload)
            self.assertEqual(first, self.call('/api/assess', payload))
            payload['answer'] = 'A different response'
            with self.assertRaises(HTTPError) as error:
                self.call('/api/assess', payload)
            self.assertEqual(error.exception.code, 400)
            error.exception.close()
            self.assertEqual(model.call_count, 1)

    def test_history_revision_review_and_session_isolation(self):
        identifier = str(uuid4())
        with patch('run.review', side_effect=lambda a,c,b: assess(a,c)):
            self.call('/api/assess', {'id':identifier,'case_id':'initial','answer':'We will verify the documents.'})
        self.call('/api/revision', {'id':identifier,'revision':'Please share an order number and damage photo.'})
        self.call('/api/review', {'id':identifier,'note':'Needs another case.','verdict':'needs_practice'})
        row = self.call('/api/history')['attempts'][0]
        self.assertEqual(row['verdict'], 'needs_practice')
        self.assertTrue(row['revision'])
        self.assertEqual(self.call('/api/history', cookie='')['attempts'], [])
        with self.assertRaises(HTTPError) as error:
            self.call('/api/review', {'id':identifier,'note':'Not my session.','verdict':'ready'}, cookie='')
        self.assertEqual(error.exception.code, 400)
        error.exception.close()

    def test_unexpected_origin_rejected_before_model(self):
        with patch('run.review') as model:
            with self.assertRaises(HTTPError) as error:
                self.call('/api/assess', {'id':str(uuid4()),'case_id':'initial','answer':'Hello'}, origin='https://unexpected.invalid')
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
            model.assert_not_called()

if __name__ == '__main__':
    unittest.main()
