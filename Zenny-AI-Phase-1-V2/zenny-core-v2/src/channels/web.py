"""
Web Widget Channel Adapter
Primary chat interface. Simple passthrough.
"""

from src.types import NormalizedMessage


class WebAdapter:
    """Web widget adapter — minimal transformation needed."""

    def normalize(self, payload: dict) -> NormalizedMessage:
        """Normalize web widget payload to internal format."""
        return NormalizedMessage(
            channel="web",
            client_id=payload.get("client_id", ""),
            user_id=payload.get("user_id", payload.get("session_id", "anonymous")),
            message=payload.get("message", ""),
            metadata={
                "user_agent": payload.get("user_agent"),
                "page_url": payload.get("page_url"),
                **payload.get("metadata", {}),
            },
        )

    def format_response(self, content: str, metadata: dict = None) -> dict:
        """Format response for web widget."""
        return {
            "text": content,
            "type": "text",
            "metadata": metadata or {},
        }
