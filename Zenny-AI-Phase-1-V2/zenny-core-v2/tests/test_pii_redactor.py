"""
PII Redactor Tests
"""

import pytest
from src.services.pii_redactor import pii_redactor


def test_credit_card_redacted():
    text = "My card is 4111-1111-1111-1111"
    result = pii_redactor.redact(text)
    assert "[REDACTED_CC]" in result
    assert "4111" not in result


def test_ssn_redacted():
    text = "My SSN is 123-45-6789"
    result = pii_redactor.redact(text)
    assert "[REDACTED_SSN]" in result


def test_phone_redacted():
    text = "Call me at +1 555-123-4567"
    result = pii_redactor.redact(text)
    assert "[REDACTED_PHONE]" in result


def test_email_redacted():
    text = "Email me at john@store.com"
    result = pii_redactor.redact(text)
    assert "[REDACTED_EMAIL]" in result


def test_no_pii_preserved():
    text = "Hello, I need help with my order"
    result = pii_redactor.redact(text)
    assert result == text


def test_has_pii_detection():
    assert pii_redactor.has_pii("My card is 4111-1111-1111-1111") is True
    assert pii_redactor.has_pii("Hello world") is False
