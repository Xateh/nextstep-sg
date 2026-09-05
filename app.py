"""HTTP-independent API plus a loopback-only development interface."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import time

VERSION = '0.1.0'
MAX_BODY = 65536
LOCAL_KEY = secrets.token_bytes(32)


class ApiError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def signing_key():
    key = os.environ.get('PLAN_SIGNING_KEY', '')
    if key:
        if len(key) < 32:
            raise RuntimeError('Plan signing configuration is invalid')
        return key.encode()
    if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        raise RuntimeError('Plan signing configuration is missing')
    return LOCAL_KEY


def seal(plan, principal='local', reviewed=False, expires_at=None):
    envelope = {'plan': plan, 'reviewed': reviewed,
                'expires_at': int(time.time()) + 1800 if expires_at is None else expires_at,
                'principal': hashlib.sha256(principal.encode()).hexdigest()}
    envelope['signature'] = hmac.new(signing_key(), canonical(envelope), hashlib.sha256).hexdigest()
    return envelope


def verify(envelope, principal):
    if not isinstance(envelope, dict) or set(envelope) != {'plan', 'reviewed', 'expires_at', 'principal', 'signature'}:
        raise ApiError(400, 'Send the complete, unchanged plan envelope.')
    unsigned = {k: v for k, v in envelope.items() if k != 'signature'}
    expected = hmac.new(signing_key(), canonical(unsigned), hashlib.sha256).hexdigest()
    if not isinstance(envelope['signature'], str) or not hmac.compare_digest(envelope['signature'], expected):
        raise ApiError(400, 'Plan was changed. Generate and review a new plan.')
    if envelope['principal'] != hashlib.sha256(principal.encode()).hexdigest():
        raise ApiError(403, 'This plan belongs to a different AWS session. Generate a new plan.')
    if type(envelope['expires_at']) is not int or envelope['expires_at'] <= int(time.time()):
        raise ApiError(410, 'This plan expired. Generate and review a new plan.')
    return envelope


def export_markdown(plan):
    lines = ['# My next-step plan', '', 'Synthetic demonstration only. Not an eligibility or employment assessment.',
             '', 'Mode: ' + str(plan['mode']), '', '## Goal', '', str(plan['profile'].get('goal', '')), '']
    for index, action in enumerate(plan['actions'], 1):
        lines += [f"## {index}. {action['title']}", '', action['next_step'], '',
                  'Source: ' + action['source_url'], '', 'Checks before acting:']
        lines += ['- ' + str(check) for check in action.get('checks', [])]
        lines.append('')
    lines += ['## Still unresolved', ''] + ['- ' + str(question) for question in plan.get('questions', [])]
    lines += ['', 'Reviewed document only. Nothing was sent, applied for or booked.']
    return '\n'.join(lines)


def dispatch(method, path, payload=None, principal='local'):
    try:
        if method == 'GET' and path == '/health':
            return 200, {'status': 'ok', 'version': VERSION, 'data_policy': 'synthetic-only',
                         'default_mode': os.environ.get('PLANNER_MODE', 'offline')}
        if method == 'GET' and path == '/v1/resources':
            from planner import load_catalog
            return 200, {'resources': load_catalog()}
        if method != 'POST' or path not in {'/v1/plans', '/v1/plans/review', '/v1/plans/export'}:
            raise ApiError(404, 'Endpoint not found.')
        if not isinstance(payload, dict):
            raise ApiError(400, 'Request body must be a JSON object.')
        if path == '/v1/plans':
            if set(payload) - {'profile', 'mode'}:
                raise ApiError(400, 'Unknown request fields.')
            from planner import create_plan
            mode = payload.get('mode', os.environ.get('PLANNER_MODE', 'offline'))
            plan = create_plan(payload.get('profile'), mode=mode)
            return 200, seal(plan, principal)
        if set(payload) - ({'envelope', 'approved'} if path.endswith('/review') else {'envelope'}):
            raise ApiError(400, 'Unknown request fields.')
        envelope = verify(payload.get('envelope'), principal)
        if path.endswith('/review'):
            if payload.get('approved') is not True:
                raise ApiError(400, 'Explicit approval is required.')
            if not envelope['plan'].get('actions'):
                raise ApiError(409, 'Resolve the questions and generate an actionable plan first.')
            return 200, seal(envelope['plan'], principal, reviewed=True, expires_at=envelope['expires_at'])
        if envelope['reviewed'] is not True:
            raise ApiError(409, 'Review this exact plan before exporting it.')
        return 200, {'filename': 'transition-plan.md', 'content': export_markdown(envelope['plan'])}
    except ApiError as error:
        return error.status, {'error': error.message}
    except (ValueError, TypeError, KeyError, OverflowError):
        return 400, {'error': 'Invalid request. Check the documented fields and use synthetic data only.'}
    except RuntimeError:
        return 503, {'error': 'Planner unavailable. Check AWS session, model access and configuration. No live result was fabricated.'}


def serve(port=8765):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import urlsplit
    static = Path(__file__).parent / 'static'

    class Handler(BaseHTTPRequestHandler):
        # ponytail: single-user loopback server; use a hardened gateway before public hosting.
        def log_message(self, *_):
            pass  # Never log request bodies, credentials or profile text.

        def reply(self, status, body, content_type='application/json; charset=utf-8'):
            data = canonical(body) if isinstance(body, dict) else body
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(data)

        def allowed_host(self):
            return self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}

        def api(self, method, path, payload=None):
            if os.environ.get('MVP_API_URL'):
                try:
                    from scripts.aws_client import call_api
                    return call_api(method, path, payload)
                except Exception:
                    return 503, {'error': 'Shared AWS endpoint unavailable. Refresh temporary AWS credentials and verify MVP_API_URL.'}
            return dispatch(method, path, payload)

        def do_GET(self):
            if not self.allowed_host():
                return self.reply(403, {'error': 'Use the loopback application address.'})
            path = urlsplit(self.path).path
            names = {'/': ('index.html', 'text/html; charset=utf-8'),
                     '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                     '/style.css': ('style.css', 'text/css; charset=utf-8')}
            if path in names:
                name, mime = names[path]
                if not (static / name).is_file():
                    return self.reply(503, {'error': 'Interface files unavailable.'})
                return self.reply(200, (static / name).read_bytes(), mime)
            return self.reply(*self.api('GET', path))

        def do_POST(self):
            origin = self.headers.get('Origin')
            if not self.allowed_host() or (origin and origin not in {f'http://localhost:{port}', f'http://127.0.0.1:{port}'}):
                return self.reply(403, {'error': 'Cross-origin requests are not allowed.'})
            if self.headers.get('X-SimplifyNext-Client') != '1':
                return self.reply(403, {'error': 'Missing local client header.'})
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.reply(415, {'error': 'Use application/json.'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= MAX_BODY:
                    return self.reply(413, {'error': 'JSON request must be between 1 and 65536 bytes.'})
                payload = json.loads(self.rfile.read(length), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            except (ValueError, UnicodeError):
                return self.reply(400, {'error': 'Invalid JSON.'})
            return self.reply(*self.api('POST', urlsplit(self.path).path, payload))

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'SimplifyNext MVP: http://127.0.0.1:{port} (synthetic data only)', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    serve(parser.parse_args().port)
