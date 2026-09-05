import copy
import importlib
import os
import time
import unittest


class ApiTests(unittest.TestCase):
    def setUp(self):
        # Removing API implementation must fail, not accidentally skip this suite.
        try:
            self.api = importlib.import_module('app')
        except ModuleNotFoundError:
            self.api = None
        self.assertIsNotNone(self.api, 'The API has not been implemented')
        self.plan = {'mode': 'offline', 'status': 'draft', 'profile': {'goal': 'Explore work'},
                     'actions': [{'resource_id': 's2w', 'title': 'School-to-Work',
                                  'next_step': 'Discuss with your school',
                                  'source_url': 'https://www.enablingguide.sg/',
                                  'checks': ['School must confirm suitability']}],
                     'questions': [], 'trace': []}

    def test_health_reports_demo_boundary(self):
        status, body = self.api.dispatch('GET', '/health')
        self.assertEqual(status, 200)
        self.assertEqual(body['data_policy'], 'synthetic-only')

    def test_export_requires_review(self):
        envelope = self.api.seal(self.plan, principal='alice')
        status, _ = self.api.dispatch('POST', '/v1/plans/export', {'envelope': envelope}, 'alice')
        self.assertEqual(status, 409)

    def test_review_binds_exact_document_and_principal(self):
        envelope = self.api.seal(self.plan, principal='alice')
        status, result = self.api.dispatch('POST', '/v1/plans/review',
                                         {'envelope': envelope, 'approved': True}, 'alice')
        self.assertEqual(status, 200)
        status, exported = self.api.dispatch('POST', '/v1/plans/export', {'envelope': result}, 'alice')
        self.assertEqual(status, 200)
        self.assertIn('School must confirm suitability', exported['content'])
        changed = copy.deepcopy(result)
        changed['plan']['actions'][0]['next_step'] = 'Guaranteed job'
        self.assertEqual(self.api.dispatch('POST', '/v1/plans/export', {'envelope': changed}, 'alice')[0], 400)
        self.assertEqual(self.api.dispatch('POST', '/v1/plans/export', {'envelope': result}, 'bob')[0], 403)

    def test_declined_review_not_accepted(self):
        envelope = self.api.seal(self.plan)
        self.assertEqual(self.api.dispatch('POST', '/v1/plans/review',
                         {'envelope': envelope, 'approved': False})[0], 400)

    def test_expired_document_cannot_be_exported(self):
        envelope = self.api.seal(self.plan, reviewed=True, expires_at=int(time.time()) - 1)
        self.assertEqual(self.api.dispatch('POST', '/v1/plans/export', {'envelope': envelope})[0], 410)

    def test_unknown_route_and_bad_payload_are_errors(self):
        self.assertEqual(self.api.dispatch('POST', '/v1/delete-everything', {})[0], 404)
        self.assertEqual(self.api.dispatch('POST', '/v1/plans/review', []) [0], 400)

    def test_lambda_rejects_missing_iam_identity(self):
        handler = importlib.import_module('lambda_function').handler
        result = handler({'version': '2.0', 'rawPath': '/health',
                          'requestContext': {'http': {'method': 'GET'}}}, None)
        self.assertEqual(result['statusCode'], 401)

    def test_lambda_rejects_null_authorizer(self):
        handler = importlib.import_module('lambda_function').handler
        for authorizer in (None, {'iam': None}):
            event = {'rawPath': '/health', 'requestContext': {'http': {'method': 'GET'}, 'authorizer': authorizer}}
            self.assertEqual(handler(event, None)['statusCode'], 401)

    def test_lambda_authenticated_health_and_invalid_json(self):
        handler = importlib.import_module('lambda_function').handler
        event = {'version': '2.0', 'rawPath': '/health', 'requestContext': {
            'http': {'method': 'GET'}, 'authorizer': {'iam': {'userArn': 'arn:aws:sts::000000000000:assumed-role/demo/test'}}}}
        self.assertEqual(handler(event, None)['statusCode'], 200)
        event.update(rawPath='/v1/plans', body='{oops')
        event['requestContext']['http']['method'] = 'POST'
        event['headers'] = {'content-type': 'application/json'}
        self.assertEqual(handler(event, None)['statusCode'], 400)


if __name__ == '__main__':
    unittest.main()
