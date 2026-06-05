"""Tests for HTTP origin header validation in POST endpoints.

Verifies that _is_allowed_origin() blocks hostile prefix domains,
wrong ports, and external origins while allowing exact same-origin.
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import _is_allowed_origin

HOST = "127.0.0.1"
PORT = 8765


class TestOriginAllowed:
    def test_exact_match_allowed(self):
        assert _is_allowed_origin(f"http://{HOST}:{PORT}", HOST, PORT) is True

    def test_empty_origin_allowed(self):
        # No Origin header = same-origin browser request or non-browser client
        assert _is_allowed_origin("", HOST, PORT) is True

    def test_localhost_same_port_allowed(self):
        # Learners naturally type localhost; it must reach the POST APIs
        assert _is_allowed_origin(f"http://localhost:{PORT}", HOST, PORT) is True

    def test_localhost_wrong_port_blocked(self):
        assert _is_allowed_origin("http://localhost:9999", HOST, PORT) is False


class TestOriginBlocked:
    def test_hostile_prefix_domain_blocked(self):
        # P0 bug: http://127.0.0.1.evil.com starts with http://127.0.0.1
        assert _is_allowed_origin(f"http://{HOST}.evil.com", HOST, PORT) is False

    def test_wrong_port_blocked(self):
        assert _is_allowed_origin(f"http://{HOST}:9999", HOST, PORT) is False

    def test_default_port_80_blocked(self):
        # http://127.0.0.1 with no port → port 80, not 8765
        assert _is_allowed_origin(f"http://{HOST}", HOST, PORT) is False

    def test_external_domain_blocked(self):
        assert _is_allowed_origin("http://evil.com", HOST, PORT) is False

    def test_https_scheme_blocked(self):
        assert _is_allowed_origin(f"https://{HOST}:{PORT}", HOST, PORT) is False

    def test_null_origin_string_blocked(self):
        # "null" is sent by sandboxed iframes — should be rejected
        assert _is_allowed_origin("null", HOST, PORT) is False

    def test_malformed_origin_blocked(self):
        assert _is_allowed_origin("not-a-url", HOST, PORT) is False
