"""
WhatsApp Business Channel Adapter
Twilio or 360dialog API wrapper.
"""

from src.types import NormalizedMessage


class WhatsAppAdapter:
    """
    WhatsApp Business API adapter.
    Supports Twilio and 360dialog.
    """

    def __init__(self, provider: str = "twilio"):
        self.provider = provider

    def normalize(self, payload: dict) -> NormalizedMessage:
        """
        Normalize WhatsApp webhook payload.

        Twilio payload:
            {
                "From": "whatsapp:+1234567890",
                "Body": "Where is my order?",
                "MessageSid": "SMxxx",
                "ProfileName": "John Doe",
            }

        360dialog payload:
            {
                "messages": [{
                    "from": "1234567890",
                    "text": {"body": "Where is my order?"},
                    "timestamp": "1234567890",
                }]
            }
        """
        if self.provider == "twilio":
            from_number = payload.get("From", "").replace("whatsapp:", "")
            text = payload.get("Body", "")
            profile_name = payload.get("ProfileName", "")
            message_id = payload.get("MessageSid", "")
        else:  # 360dialog
            messages = payload.get("messages", [{}])
            msg = messages[0] if messages else {}
            from_number = msg.get("from", "")
            text = msg.get("text", {}).get("body", "")
            profile_name = msg.get("sender", {}).get("name", "")
            message_id = msg.get("id", "")

        return NormalizedMessage(
            channel="whatsapp",
            client_id=payload.get("client_id", ""),
            user_id=f"whatsapp:{from_number}",
            message=text,
            metadata={
                "phone": from_number,
                "profile_name": profile_name,
                "message_id": message_id,
                "provider": self.provider,
            },
        )

    def format_response(self, content: str, metadata: dict = None) -> dict:
        """Format response for WhatsApp."""
        # WhatsApp supports text, media, templates
        return {
            "text": content,
            "type": "text",
            "metadata": metadata or {},
        }

    def format_delivery_receipt(self, message_id: str, status: str) -> dict:
        """Format delivery status update."""
        return {
            "message_id": message_id,
            "status": status,  # sent, delivered, read, failed
        }
