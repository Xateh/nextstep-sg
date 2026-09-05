import io
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from botocore.credentials import Credentials


VALID_URL = "https://abc123.lambda-url.ap-southeast-1.on.aws/"


class _Session:
    def __init__(self, credentials):
        self.credentials = credentials

    def get_credentials(self):
        return self.credentials


class _Response:
    status = 200

    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.body


class AwsClientTests(unittest.TestCase):
    def setUp(self):
        try:
            from scripts import aws_client
        except ImportError:
            aws_client = None
        self.client = aws_client
        self.assertIsNotNone(aws_client, "AWS client has not been implemented")

    def test_rejects_non_function_urls_and_url_components(self):
        invalid = [
            "http://abc123.lambda-url.ap-southeast-1.on.aws/",
            "https://example.com/",
            "https://user:pass@abc123.lambda-url.ap-southeast-1.on.aws/",
            "https://abc123.lambda-url.ap-southeast-1.on.aws:443/",
            "https://abc123.lambda-url.ap-southeast-1.on.aws/path",
            "https://abc123.lambda-url.ap-southeast-1.on.aws/?query=1",
            "https://abc123.lambda-url.ap-southeast-1.on.aws/#fragment",
            "https://abc123.lambda-url.not-a-region.on.aws/",
        ]
        for url in invalid:
            with self.subTest(url=url), patch.dict(os.environ, {"MVP_API_URL": url}, clear=False):
                with self.assertRaises(ValueError):
                    self.client.call_api("GET", "/health")

    def test_missing_temporary_credentials_fails_before_transport(self):
        with patch.dict(os.environ, {"MVP_API_URL": VALID_URL}, clear=False), patch.object(
            self.client.boto3, "Session", return_value=_Session(None)
        ), patch.object(self.client, "_send", side_effect=AssertionError("transport called")):
            with self.assertRaisesRegex(RuntimeError, "Temporary AWS credentials"):
                self.client.call_api("GET", "/health")

    def test_permanent_credentials_are_rejected(self):
        credentials = Credentials("AKIATEST", "secret")
        with patch.dict(os.environ, {"MVP_API_URL": VALID_URL}, clear=False), patch.object(
            self.client.boto3, "Session", return_value=_Session(credentials)
        ):
            with self.assertRaisesRegex(RuntimeError, "Temporary AWS credentials"):
                self.client.call_api("GET", "/health")

    def test_exact_body_is_signed_for_lambda_with_content_headers(self):
        payload = {"profile": {"synthetic": True, "goal": "Explore work"}, "mode": "offline"}
        expected = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        captured = {}

        def send(request, timeout):
            captured.update(request=request, timeout=timeout)
            return _Response({"plan": {"profile": {"synthetic": True}}})

        credentials = Credentials("ASIATESTACCESS", "test-secret", "test-session-token")
        with patch.dict(os.environ, {"MVP_API_URL": VALID_URL}, clear=False), patch.object(
            self.client.boto3, "Session", return_value=_Session(credentials)
        ), patch.object(self.client, "_send", side_effect=send):
            status, body = self.client.call_api("POST", "/v1/plans", payload)

        request = captured["request"]
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual((status, body), (200, {"plan": {"profile": {"synthetic": True}}}))
        self.assertEqual(request.data, expected)
        self.assertEqual(captured["timeout"], 90)
        self.assertEqual(headers["content-type"], "application/json")
        self.assertEqual(headers["x-amz-content-sha256"], hashlib.sha256(expected).hexdigest())
        self.assertEqual(headers["x-amz-security-token"], "test-session-token")
        self.assertIn("Credential=ASIATESTACCESS/", headers["authorization"])
        self.assertIn("/ap-southeast-1/lambda/aws4_request", headers["authorization"])
        self.assertIn(
            "SignedHeaders=content-type;host;x-amz-content-sha256;x-amz-date;x-amz-security-token",
            headers["authorization"],
        )

    def test_http_json_errors_are_sanitized(self):
        error = HTTPError(
            VALID_URL,
            400,
            "bad",
            {},
            io.BytesIO(b'{"error":"Invalid request.","debug":"Authorization: secret"}'),
        )
        credentials = Credentials("ASIATESTACCESS", "test-secret", "test-session-token")
        with patch.dict(os.environ, {"MVP_API_URL": VALID_URL}, clear=False), patch.object(
            self.client.boto3, "Session", return_value=_Session(credentials)
        ), patch.object(self.client, "_send", side_effect=error):
            status, body = self.client.call_api("POST", "/v1/plans", {})

        self.assertEqual(status, 400)
        self.assertEqual(body, {"error": "Invalid request."})
        self.assertNotIn("secret", json.dumps(body).lower())

    def test_redirect_response_is_rejected(self):
        error = HTTPError(VALID_URL, 302, "Found", {"Location": "https://example.com"}, io.BytesIO(b""))
        credentials = Credentials("ASIATESTACCESS", "test-secret", "test-session-token")
        with patch.dict(os.environ, {"MVP_API_URL": VALID_URL}, clear=False), patch.object(
            self.client.boto3, "Session", return_value=_Session(credentials)
        ), patch.object(self.client, "_send", side_effect=error):
            status, body = self.client.call_api("GET", "/health")

        self.assertEqual(status, 302)
        self.assertEqual(body, {"error": "Redirects are not allowed for signed AWS requests."})
        self.assertIsNone(self.client._NoRedirect().redirect_request(None, None, 302, "Found", {}, VALID_URL))

    def test_only_documented_route_and_method_pairs_are_allowed(self):
        with patch.dict(os.environ, {"MVP_API_URL": VALID_URL}, clear=False):
            for method, path in [("POST", "/health"), ("GET", "/v1/plans"), ("GET", "/unknown")]:
                with self.subTest(method=method, path=path), self.assertRaises(ValueError):
                    self.client.call_api(method, path)

    def test_output_file_accepts_only_synthetic_plan_envelopes(self):
        envelope = {
            "plan": {"profile": {"synthetic": True}},
            "signature": "not-a-credential",
            "reviewed": False,
            "expires_at": 1,
            "principal": "hash",
        }
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "plan.json"
            self.client._write_envelope(target, envelope)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), envelope)
            with self.assertRaises(ValueError):
                self.client._write_envelope(target, {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
