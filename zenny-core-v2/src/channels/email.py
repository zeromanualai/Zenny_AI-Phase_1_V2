"""
Email Channel Adapter
SendGrid inbound parse + HTML-to-text conversion.
"""

import re
from html import unescape
from src.types import NormalizedMessage


class EmailAdapter:
    """
    Email adapter.
    Handles SendGrid inbound parse webhook.
    Converts HTML to plain text.
    Tracks thread IDs for conversation continuity.
    """

    def normalize(self, payload: dict) -> NormalizedMessage:
        """
        Normalize SendGrid inbound parse payload.

        SendGrid payload:
            {
                "from": "john@store.com",
                "to": "support@zenny.zeromanual.com",
                "subject": "Order question",
                "text": "Where is my order?",
                "html": "<p>Where is my order?</p>",
                "headers": "...",
            }
        """
        from_email = payload.get("from", "")
        # Extract email from "Name <email>" format
        email_match = re.search(r"<([^>]+)>", from_email)
        clean_email = email_match.group(1) if email_match else from_email

        # Prefer plain text, fallback to HTML stripped
        text = payload.get("text", "")
        if not text and payload.get("html"):
            text = self._html_to_text(payload["html"])

        # Extract thread ID from headers or subject
        thread_id = self._extract_thread_id(payload)

        return NormalizedMessage(
            channel="email",
            client_id=payload.get("client_id", ""),
            user_id=f"email:{clean_email}",
            message=text.strip(),
            metadata={
                "email": clean_email,
                "subject": payload.get("subject", ""),
                "to": payload.get("to", ""),
                "thread_id": thread_id,
                "message_id": payload.get("dkim", ""),  # Use DKIM as unique ID
            },
        )

    def format_response(self, content: str, metadata: dict = None) -> dict:
        """Format response for email reply."""
        subject = metadata.get("subject", "") if metadata else ""
        thread_id = metadata.get("thread_id", "") if metadata else ""

        # Prepend Re: if not already
        if subject and not subject.startswith("Re:"):
            subject = f"Re: {subject}"

        return {
            "text": content,
            "html": f"<html><body><p>{content.replace(chr(10), '</p><p>')}</p></body></html>",
            "subject": subject,
            "thread_id": thread_id,
            "type": "email",
        }

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        # Remove scripts and styles
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        # Replace block elements with newlines
        text = re.sub(r"</(p|div|br|h[1-6]|li)>", "\n", text)
        text = re.sub(r"<li>", "- ", text)
        # Remove remaining tags
        text = re.sub(r"<[^>]+>", "", text)
        # Unescape HTML entities
        text = unescape(text)
        # Clean up whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()

    def _extract_thread_id(self, payload: dict) -> str:
        """Extract conversation thread ID from email headers."""
        headers = payload.get("headers", "")
        # Look for References or In-Reply-To header
        ref_match = re.search(r"References:\s*([^\r\n]+)", headers)
        if ref_match:
            return ref_match.group(1).strip().split()[0]
        # Fallback: use Message-ID
        msg_match = re.search(r"Message-ID:\s*<([^>]+)>", headers)
        if msg_match:
            return msg_match.group(1)
        # Final fallback: hash of subject + from
        subject = payload.get("subject", "")
        from_email = payload.get("from", "")
        import hashlib
        return hashlib.md5(f"{subject}:{from_email}".encode()).hexdigest()[:16]
