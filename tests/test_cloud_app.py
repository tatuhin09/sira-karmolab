"""Offline checks for the hosted WSGI entry point."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assessment import assess
from cloud_app import create_app

class CloudTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'practice.sqlite3'
        self.app = create_app(self.path, public_host='demo.example')
        self.client = self.app.test_client()
        self.base = 'https://demo.example'

    def test_health_policy_cookie_and_host(self):
        self.assertEqual(self.client.get('/healthz', base_url=self.base).status_code,200)
        response = self.client.get('/api/policy', base_url=self.base)
        self.assertEqual(response.json['result']['status'],'completed')
        self.assertEqual(len(response.json['result']['records']),3)
        self.assertIn('Secure',response.headers['Set-Cookie'])
        self.assertIn('HttpOnly',response.headers['Set-Cookie'])
        self.assertEqual(self.client.get('/healthz',base_url='https://wrong.example').status_code,403)

    def test_idempotence_and_persistence_across_app_restart(self):
        self.client.get('/api/policy',base_url=self.base)
        payload={'id':str(uuid4()),'case_id':'initial','answer':'Please share an order number and photo.'}
        with patch('cloud_app.review',side_effect=lambda a,c,b:assess(a,c)) as model:
            first=self.client.post('/api/assess',json=payload,base_url=self.base)
            self.assertEqual(first.status_code,200)
            self.assertEqual(first.json,self.client.post('/api/assess',json=payload,base_url=self.base).json)
            self.assertEqual(model.call_count,1)
        self.client.post('/api/revision',json={'id':payload['id'],'revision':'We will verify the documents.'},base_url=self.base)
        cookie=self.client.get_cookie('karmolab',domain='demo.example').value
        other=create_app(self.path,public_host='demo.example').test_client()
        self.assertEqual(other.get('/api/history',base_url=self.base).json['attempts'],[])
        other.set_cookie('karmolab',cookie,domain='demo.example')
        rows=other.get('/api/history',base_url=self.base).json['attempts']
        self.assertEqual(rows[0]['revision'],'We will verify the documents.')

    def test_bad_origin_body_and_secret_paths(self):
        with patch('cloud_app.review') as model:
            response=self.client.post('/api/assess',json={},base_url=self.base,headers={'Origin':'https://wrong.example'})
            self.assertEqual(response.status_code,403)
            response=self.client.post('/api/assess',data='not json',content_type='application/json',base_url=self.base)
            self.assertEqual(response.status_code,400)
            response=self.client.post('/api/assess',data='x'*16001,content_type='application/json',base_url=self.base)
            self.assertEqual(response.status_code,413)
            model.assert_not_called()
        for path in ['/.env','/cloud_app.py','/runtime/practice.sqlite3']:
            self.assertEqual(self.client.get(path,base_url=self.base).status_code,404)

if __name__=='__main__': unittest.main()
