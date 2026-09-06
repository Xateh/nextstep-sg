import json
import os
from html.parser import HTMLParser
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class InterfaceParser(HTMLParser):
    VOID = {'br', 'hr', 'img', 'input', 'link', 'meta'}

    def __init__(self):
        super().__init__()
        self.elements = {}
        self.stack = []
        self.text = []
        self.text_by_id = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        element_id = attrs.get('id')
        if element_id:
            self.elements[element_id] = {
                'tag': tag,
                'attrs': attrs,
                'ancestors': {item_id for _, item_id in self.stack if item_id},
            }
        if tag not in self.VOID:
            self.stack.append((tag, element_id))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.text.append(data)
        for _, element_id in self.stack:
            if element_id:
                self.text_by_id.setdefault(element_id, []).append(data)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            cls.port = sock.getsockname()[1]
        cls.url = f'http://127.0.0.1:{cls.port}'
        env = dict(os.environ, PLANNER_MODE='offline')
        env.pop('MVP_API_URL', None)
        env.pop('AWS_LAMBDA_FUNCTION_NAME', None)
        cls.process = subprocess.Popen([sys.executable, 'app.py', '--port', str(cls.port)],
                                       cwd=Path(__file__).resolve().parents[1], env=env,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                with urlopen(cls.url + '/health', timeout=1):
                    return
            except OSError:
                time.sleep(.05)
        cls.process.terminate()
        raise RuntimeError('Local HTTP server did not start')

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=5)

    def request(self, path, body=None, headers=None):
        data = None if body is None else json.dumps(body).encode()
        default = {'Content-Type': 'application/json', 'X-SimplifyNext-Client': '1'}
        default.update(headers or {})
        request = Request(self.url + path, data=data, headers=default)
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.headers, response.read()

    def test_interface_and_assets_are_served_with_safe_headers(self):
        for path, fragment in [('/', b'Supported next steps'), ('/app.js', b'fetch('), ('/style.css', b'focus-visible')]:
            status, headers, body = self.request(path)
            self.assertEqual(status, 200, path)
            self.assertIn(fragment, body)
            self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
            self.assertEqual(headers['Cache-Control'], 'no-store')

    def test_interface_exposes_three_stages_and_linked_controls(self):
        status, _, body = self.request('/')
        self.assertEqual(status, 200)
        document = InterfaceParser()
        document.feed(body.decode())
        text = ' '.join(' '.join(document.text).split())

        for stage in ('01 / PROFILE', '02 / REVIEW NEXT STEPS', '03 / DOWNLOAD REVIEWED PLAN'):
            self.assertIn(stage, text)
        self.assertEqual(document.elements['plan-title']['attrs'].get('tabindex'), '-1')

        edit = document.elements['edit-profile']
        self.assertEqual((edit['tag'], edit['attrs'].get('type')), ('button', 'button'))
        self.assertIn('result', edit['ancestors'])
        reset = document.elements['reset-profile']
        self.assertEqual((reset['tag'], reset['attrs'].get('type')), ('button', 'button'))
        self.assertNotIn('profile-fields', reset['ancestors'])
        self.assertIn('result', document.elements['plan-expiry']['ancestors'])

        linked_hints = {
            'goal': {'goal-hint'},
            'interests': {'interests-hint'},
            'hours': {'constraint-hint'},
            'budget': {'constraint-hint'},
            'approval': {'review-hint', 'plan-expiry'},
        }
        for control, expected in linked_hints.items():
            described_by = set(document.elements[control]['attrs'].get('aria-describedby', '').split())
            self.assertTrue(expected.issubset(described_by), control)
            self.assertTrue(expected.issubset(document.elements), control)
        constraint_hint = ' '.join(document.text_by_id['constraint-hint']).lower()
        self.assertIn('blank', constraint_hint)
        self.assertIn('unknown', constraint_hint)
        self.assertIn('0', constraint_hint)

    def test_actual_create_review_export(self):
        profile = {'goal': 'Explore office skills', 'strengths': 'Organising files',
                   'interests': ['office'], 'full_time_student': False,
                   'weekly_hours': 3, 'budget_sgd': 0, 'synthetic': True}
        status, _, raw = self.request('/v1/plans', {'profile': profile, 'mode': 'offline'})
        self.assertEqual(status, 200)
        draft = json.loads(raw)
        self.assertFalse(draft['reviewed'])
        self.assertTrue(draft['plan']['actions'])
        self.assertEqual(self.request('/v1/plans/export', {'envelope': draft})[0], 409)
        status, _, raw = self.request('/v1/plans/review', {'envelope': draft, 'approved': True})
        self.assertEqual(status, 200)
        reviewed = json.loads(raw)
        status, _, raw = self.request('/v1/plans/export', {'envelope': reviewed})
        self.assertEqual(status, 200)
        self.assertIn('Nothing was sent', json.loads(raw)['content'])
        reviewed['plan']['profile']['goal'] = 'Changed after review'
        self.assertEqual(self.request('/v1/plans/export', {'envelope': reviewed})[0], 400)

    def test_origin_host_header_and_path_boundaries(self):
        self.assertEqual(self.request('/v1/plans', {}, {'Origin': 'https://attacker.example'})[0], 403)
        self.assertEqual(self.request('/v1/plans', {}, {'X-SimplifyNext-Client': ''})[0], 403)
        self.assertEqual(self.request('/health', headers={'Host': 'attacker.example'})[0], 403)
        self.assertEqual(self.request('/../app.py')[0], 404)
        self.assertEqual(self.request('/v1/plans', {}, {'Content-Type': 'text/plain'})[0], 415)


if __name__ == '__main__':
    unittest.main()
