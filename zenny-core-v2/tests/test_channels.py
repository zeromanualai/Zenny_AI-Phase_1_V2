"""
Channel Adapter Tests
"""

import pytest
from src.channels.web import WebAdapter
from src.channels.whatsapp import WhatsAppAdapter
from src.channels.email import EmailAdapter
from src.channels.messenger import MessengerAdapter


class TestWebAdapter:
    def test_normalize(self):
        adapter = WebAdapter()
        payload = {
            "client_id": "test-store",
            "user_id": "user-123",
            "message": "Hello",
            "user_agent": "Mozilla/5.0",
        }
        result = adapter.normalize(payload)
        assert result.channel == "web"
        assert result.user_id == "user-123"
        assert result.message == "Hello"

    def test_format_response(self):
        adapter = WebAdapter()
        result = adapter.format_response("Hi there")
        assert result["text"] == "Hi there"
        assert result["type"] == "text"


class TestWhatsAppAdapter:
    def test_normalize_twilio(self):
        adapter = WhatsAppAdapter(provider="twilio")
        payload = {
            "client_id": "test-store",
            "From": "whatsapp:+1234567890",
            "Body": "Where is my order?",
            "ProfileName": "John",
        }
        result = adapter.normalize(payload)
        assert result.channel == "whatsapp"
        assert result.user_id == "whatsapp:+1234567890"
        assert result.message == "Where is my order?"
        assert result.metadata["profile_name"] == "John"

    def test_normalize_360dialog(self):
        adapter = WhatsAppAdapter(provider="360dialog")
        payload = {
            "client_id": "test-store",
            "messages": [{
                "from": "1234567890",
                "text": {"body": "Hello"},
            }],
        }
        result = adapter.normalize(payload)
        assert result.channel == "whatsapp"
        assert result.user_id == "whatsapp:1234567890"


class TestEmailAdapter:
    def test_normalize(self):
        adapter = EmailAdapter()
        payload = {
            "client_id": "test-store",
            "from": "John <john@store.com>",
            "subject": "Order question",
            "text": "Where is my order?",
        }
        result = adapter.normalize(payload)
        assert result.channel == "email"
        assert result.user_id == "email:john@store.com"
        assert result.message == "Where is my order?"

    def test_html_to_text(self):
        adapter = EmailAdapter()
        html = "<p>Hello</p><p>World</p>"
        result = adapter._html_to_text(html)
        assert "Hello" in result
        assert "World" in result


class TestMessengerAdapter:
    def test_normalize(self):
        adapter = MessengerAdapter()
        payload = {
            "client_id": "test-store",
            "entry": [{
                "id": "page-123",
                "messaging": [{
                    "sender": {"id": "user-456"},
                    "recipient": {"id": "page-123"},
                    "message": {"mid": "mid.123", "text": "Hello"},
                }],
            }],
        }
        result = adapter.normalize(payload)
        assert result.channel == "messenger"
        assert result.user_id == "messenger:user-456"
        assert result.message == "Hello"
