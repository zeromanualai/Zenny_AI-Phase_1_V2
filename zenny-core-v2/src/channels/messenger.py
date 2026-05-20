"""
Meta Messenger / Instagram DM Channel Adapter
Facebook Graph API wrapper.
"""

from src.types import NormalizedMessage


class MessengerAdapter:
    """
    Meta Messenger / Instagram DM adapter.
    Uses Facebook Graph API webhook format.
    """

    def normalize(self, payload: dict) -> NormalizedMessage:
        """
        Normalize Messenger webhook payload.

        Messenger webhook entry:
            {
                "object": "page",
                "entry": [{
                    "messaging": [{
                        "sender": {"id": "123456789"},
                        "recipient": {"id": "987654321"},
                        "message": {
                            "mid": "mid.123",
                            "text": "Where is my order?",
                        },
                        "timestamp": 1234567890,
                    }]
                }]
            }
        """
        entry = payload.get("entry", [{}])[0]
        messaging = entry.get("messaging", [{}])[0]
        sender = messaging.get("sender", {})
        message = messaging.get("message", {})

        sender_id = sender.get("id", "")
        text = message.get("text", "")
        message_id = message.get("mid", "")
        timestamp = messaging.get("timestamp", 0)

        # Handle quick replies
        quick_reply = message.get("quick_reply", {})
        if quick_reply.get("payload"):
            text = quick_reply["payload"]

        return NormalizedMessage(
            channel="messenger",
            client_id=payload.get("client_id", ""),
            user_id=f"messenger:{sender_id}",
            message=text,
            metadata={
                "sender_id": sender_id,
                "recipient_id": messaging.get("recipient", {}).get("id", ""),
                "message_id": message_id,
                "timestamp": timestamp,
                "page_id": entry.get("id", ""),
            },
        )

    def format_response(self, content: str, metadata: dict = None) -> dict:
        """Format response for Messenger."""
        response = {
            "text": content,
            "type": "text",
        }

        # Add quick replies if provided in metadata
        if metadata and metadata.get("quick_replies"):
            response["quick_replies"] = [
                {
                    "content_type": "text",
                    "title": qr["title"],
                    "payload": qr["payload"],
                }
                for qr in metadata["quick_replies"]
            ]

        return response

    def format_handover(self, target_app_id: str) -> dict:
        """Format handover to human agent (Page Inbox)."""
        return {
            "recipient": {"id": "USER_ID"},
            "target_app_id": target_app_id,
            "metadata": "Handover to human agent via Zenny",
        }
