import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_review import review, reserve, validate

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.budget = Path(self.temp.name)/'budget.db'
        self.env = patch.dict(os.environ, {'KARMOLAB_AI_ENABLED':'1','GEMINI_API_KEY':'test-key',
            'KARMOLAB_GEMINI_MODEL':'test-model','KARMOLAB_AI_DAILY_LIMIT':'2'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_disabled_makes_no_request(self):
        with patch.dict(os.environ, {'KARMOLAB_AI_ENABLED':'0'}), patch('ai_review.build_opener') as network:
            self.assertEqual(review('আজই টাকা ফেরত পাবেন','initial',self.budget)['review_mode'],'local')
            network.assert_not_called()

    def test_budget_survives_new_connection(self):
        self.assertTrue(reserve(self.budget,2))
        self.assertTrue(reserve(self.budget,2))
        self.assertFalse(reserve(self.budget,2))

    def test_reject_invented_quote_and_wrong_clause(self):
        item = {'kind':'promise','quote':'invented','clause':'3','explanation':{'bn':'কারণ','en':'Reason'}}
        with self.assertRaises(ValueError): validate({'findings':[item]},'actual answer')
        item.update(quote='actual',clause='1')
        with self.assertRaises(ValueError): validate({'findings':[item]},'actual answer')

    def test_valid_response_routes_and_retains_policy(self):
        answer = 'আজই টাকা ফেরত পাবেন'
        finding = {'kind':'promise','quote':answer,'clause':'3','explanation':{'bn':'অনুমোদন ছাড়া নিশ্চয়তা।','en':'Unapproved guarantee.'}}
        payload = {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'findings':[finding]})}]}}]}
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        with patch('ai_review.build_opener') as opener:
            opener.return_value.open.return_value = response
            result = review(answer,'initial',self.budget)
        self.assertEqual(result['review_mode'],'ai')
        self.assertEqual(result['next_case'],'timing')
        self.assertEqual(result['findings'][0]['policy']['id'],'3')
        self.assertEqual(result['status'],'trainer_review_required')

    def test_failure_preserves_local_feedback(self):
        with patch('ai_review.build_opener',side_effect=OSError('provider unavailable')):
            result = review('আজই টাকা ফেরত পাবেন','initial',self.budget)
        self.assertEqual(result['review_mode'],'fallback')
        self.assertEqual(result['engine'],'local_cues')
        self.assertEqual(result['next_case'],'timing')

    def fake_response(self, payload):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return response

    def test_incomplete_response_has_safe_reason(self):
        with patch('ai_review.build_opener') as opener:
            opener.return_value.open.return_value = self.fake_response({
                'candidates':[{'finishReason':'MAX_TOKENS'}]})
            result = review('আজই টাকা ফেরত পাবেন','initial',self.budget)
            request = opener.return_value.open.call_args.args[0]
            body = json.loads(request.data)
        self.assertIn('responseSchema', body['generationConfig'])
        self.assertEqual(result['fallback_reason'],'response_incomplete')
        self.assertEqual(result['review_mode'],'fallback')

    def test_ungrounded_model_output_is_rejected(self):
        finding = {'kind':'promise','quote':'fabricated quote','clause':'3',
                   'explanation':{'bn':'কারণ','en':'Reason'}}
        payload = {'candidates':[{'finishReason':'STOP','content':{'parts':[
            {'text':json.dumps({'findings':[finding]})}]}}]}
        with patch('ai_review.build_opener') as opener:
            opener.return_value.open.return_value = self.fake_response(payload)
            result = review('আজই টাকা ফেরত পাবেন','initial',self.budget)
        self.assertEqual(result['fallback_reason'],'evidence_validation')
        self.assertEqual(result['engine'],'local_cues')
        self.assertNotIn('fabricated quote', json.dumps(result))

    def test_limit_exhaustion_never_calls_provider(self):
        reserve(self.budget,2)
        reserve(self.budget,2)
        with patch('ai_review.build_opener') as opener:
            result = review('আজই টাকা ফেরত পাবেন','initial',self.budget)
            opener.assert_not_called()
        self.assertEqual(result['fallback_reason'],'daily_limit')

if __name__ == '__main__': unittest.main()
