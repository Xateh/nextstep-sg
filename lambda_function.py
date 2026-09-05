"""Lambda Function URL adapter. Deploy only with AuthType AWS_IAM."""
import base64
import json
from app import MAX_BODY, dispatch


def handler(event, context):
    headers = {'content-type': 'application/json', 'cache-control': 'no-store',
               'x-content-type-options': 'nosniff'}
    try:
        request = event.get('requestContext', {})
        iam = (request.get('authorizer') or {}).get('iam') or {}
        principal = iam.get('userArn')
        if not principal:
            status, body = 401, {'error': 'AWS_IAM signed access is required.'}
        else:
            method = request.get('http', {}).get('method', '')
            raw = event.get('body') or ''
            if event.get('isBase64Encoded'):
                raw = base64.b64decode(raw, validate=True).decode('utf-8')
            if len(raw.encode('utf-8')) > MAX_BODY:
                status, body = 413, {'error': 'Request too large.'}
            elif method == 'POST' and event.get('headers', {}).get('content-type', '').split(';')[0] != 'application/json':
                status, body = 415, {'error': 'Use application/json.'}
            else:
                payload = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError())) if raw else None
                status, body = dispatch(method, event.get('rawPath', ''), payload, principal)
    except (ValueError, TypeError, UnicodeError):
        status, body = 400, {'error': 'Invalid request.'}
    except Exception:
        status, body = 503, {'error': 'Service unavailable. Check deployment configuration.'}
    return {'statusCode': status, 'headers': headers, 'body': json.dumps(body, allow_nan=False), 'isBase64Encoded': False}
