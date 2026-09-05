"""Bounded SigV4 client for the private SimplifyNext Lambda Function URL."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import boto3
import botocore.session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


TIMEOUT_SECONDS = 90
_HOST = re.compile(r"^[a-z0-9]+\.lambda-url\.([a-z0-9-]+)\.on\.aws$")
_ROUTES = {
    ("GET", "/health"),
    ("GET", "/v1/resources"),
    ("POST", "/v1/plans"),
    ("POST", "/v1/plans/review"),
    ("POST", "/v1/plans/export"),
}
_COMMANDS = {
    "health": ("GET", "/health"),
    "resources": ("GET", "/v1/resources"),
    "create": ("POST", "/v1/plans"),
    "review": ("POST", "/v1/plans/review"),
    "export": ("POST", "/v1/plans/export"),
}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _endpoint() -> tuple[str, str]:
    value = os.environ.get("MVP_API_URL", "")
    parsed = urlsplit(value)
    match = _HOST.fullmatch(parsed.hostname or "")
    if (
        parsed.scheme != "https"
        or not match
        or parsed.netloc != parsed.hostname
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("MVP_API_URL must be a root AWS Lambda Function URL using HTTPS.")
    region = match.group(1)
    regions = botocore.session.get_session().get_available_regions("lambda", partition_name="aws")
    if region not in regions:
        raise ValueError("MVP_API_URL contains an unsupported AWS region.")
    return value.rstrip("/"), region


def _temporary_credentials(region):
    try:
        credentials = boto3.Session(region_name=region).get_credentials()
        frozen = credentials.get_frozen_credentials() if credentials else None
    except Exception:
        raise RuntimeError("Temporary AWS credentials are unavailable or expired.") from None
    if not frozen or not frozen.access_key or not frozen.secret_key or not frozen.token:
        raise RuntimeError("Temporary AWS credentials are required; permanent keys are not accepted.")
    return frozen


def _send(request, timeout):
    return build_opener(_NoRedirect()).open(request, timeout=timeout)


def _json_object(raw):
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise RuntimeError("AWS endpoint returned an invalid JSON response.") from None
    if not isinstance(body, dict):
        raise RuntimeError("AWS endpoint returned a non-object JSON response.")
    return body


def _http_error_body(error):
    if 300 <= error.code < 400:
        return {"error": "Redirects are not allowed for signed AWS requests."}
    try:
        body = json.loads(error.read().decode("utf-8"))
        message = body.get("error") if isinstance(body, dict) else None
    except (UnicodeError, json.JSONDecodeError):
        message = None
    if (
        not isinstance(message, str)
        or not message
        or len(message) > 500
        or any(ord(character) < 32 and character not in "\t\n\r" for character in message)
        or re.search(r"authorization|credential|secret|session.?token|A[KS]IA[A-Z0-9]{8,}", message, re.I)
    ):
        message = f"AWS endpoint returned HTTP {error.code}."
    return {"error": message}


def call_api(method, path, payload=None):
    """Call one documented MVP route with temporary AWS credentials."""
    method = method.upper()
    if (method, path) not in _ROUTES:
        raise ValueError("Only documented MVP API route and method pairs are allowed.")
    if method == "GET" and payload is not None:
        raise ValueError("GET requests cannot include a body.")
    if method == "POST" and not isinstance(payload, dict):
        raise ValueError("POST requests require a JSON object body.")

    endpoint, region = _endpoint()
    if payload is None:
        body = b""
        headers = {}
    else:
        try:
            body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        except (TypeError, ValueError):
            raise ValueError("Request body must be finite JSON data.") from None
        headers = {"Content-Type": "application/json"}
    headers["X-Amz-Content-SHA256"] = hashlib.sha256(body).hexdigest()

    url = endpoint + path
    signed = AWSRequest(method=method, url=url, data=body, headers=headers)
    SigV4Auth(_temporary_credentials(region), "lambda", region).add_auth(signed)
    request = Request(url, data=body, headers=dict(signed.headers.items()), method=method)
    try:
        with _send(request, TIMEOUT_SECONDS) as response:
            return response.status, _json_object(response.read())
    except HTTPError as error:
        return error.code, _http_error_body(error)
    except (OSError, URLError):
        raise RuntimeError("AWS endpoint could not be reached.") from None


def _write_envelope(path, body):
    allowed = {"plan", "reviewed", "expires_at", "principal", "signature"}
    plan = body.get("plan") if isinstance(body, dict) and set(body) == allowed else None
    profile = plan.get("profile") if isinstance(plan, dict) else None
    if not isinstance(profile, dict) or profile.get("synthetic") is not True:
        raise ValueError("--output writes only signed synthetic plan envelopes.")
    Path(path).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_body(path):
    try:
        body = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("--body must name a readable JSON file.") from None
    if not isinstance(body, dict):
        raise ValueError("--body JSON must be an object.")
    return body


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="+", help="health, resources, create, review, export, or METHOD PATH")
    parser.add_argument("--body", help="JSON request or signed envelope file")
    parser.add_argument("--output", help="private output file for a signed synthetic plan envelope")
    args = parser.parse_args(argv)

    if len(args.target) == 1 and args.target[0] in _COMMANDS:
        command = args.target[0]
        method, path = _COMMANDS[command]
    elif len(args.target) == 2:
        command = "generic"
        method, path = args.target[0].upper(), args.target[1]
    else:
        parser.error("use a named command or METHOD PATH")

    body = _load_body(args.body) if args.body else None
    if command == "review" and body is not None:
        body = {"envelope": body, "approved": True}
    elif command == "export" and body is not None:
        body = {"envelope": body}

    try:
        status, response = call_api(method, path, body)
        if args.output and 200 <= status < 300:
            _write_envelope(args.output, response)
    except (RuntimeError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    print(json.dumps(response, indent=2, sort_keys=True))
    return 0 if 200 <= status < 300 else 1


if __name__ == "__main__":
    sys.exit(main())
