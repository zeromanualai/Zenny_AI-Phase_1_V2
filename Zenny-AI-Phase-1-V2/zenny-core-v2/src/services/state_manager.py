"""
State & Session Manager
Cross-channel session merging, slot persistence, async action handling.
"""

import time
from typing import Optional

from src.services import redis_client
from src.types import SessionState


class StateManager:
    """
    Manages conversation state across channels and turns.
    The hardest engineering problem in conversational AI.
    """

    async def get_session(
        self,
        client_id: str,
        user_id: str,
        channel: str,
    ) -> dict:
        """
        Get or create session.
        1. Check active Redis session
        2. Check cross-channel merge
        3. Initialize new session
        """
        # 1. Check Redis
        session = await redis_client.get_session(client_id, user_id, channel)
        if session:
            return session

        # 2. Cross-channel merge (try email/phone from context if available)
        # This is called separately when we have identifiers
        # For now, return new session

        # 3. New session
        return {
            "client_id": client_id,
            "user_id": user_id,
            "channel": channel,
            "slots": {},
            "intent_history": [],
            "turn_count": 0,
            "created_at": int(time.time()),
            "last_activity": int(time.time()),
        }

    async def get_or_merge_session(
        self,
        client_id: str,
        user_id: str,
        channel: str,
        identifiers: Optional[dict] = None,
    ) -> dict:
        """
        Get session with cross-channel merge attempt.
        identifiers = {"email": "john@store.com", "phone": "+1234567890"}
        """
        # Try direct session first
        session = await redis_client.get_session(client_id, user_id, channel)
        if session:
            return session

        # Try cross-channel merge
        if identifiers:
            merged = await redis_client.find_cross_channel_session(client_id, identifiers)
            if merged:
                # Save merged session under new channel key
                await redis_client.save_session(client_id, user_id, channel, merged)
                return merged

        # New session
        new_session = {
            "client_id": client_id,
            "user_id": user_id,
            "channel": channel,
            "slots": {},
            "intent_history": [],
            "turn_count": 0,
            "created_at": int(time.time()),
            "last_activity": int(time.time()),
        }
        await redis_client.save_session(client_id, user_id, channel, new_session)
        return new_session

    async def update_slots(
        self,
        client_id: str,
        user_id: str,
        channel: str,
        extracted_slots: dict,
    ) -> dict:
        """Merge new slots into existing session."""
        session = await redis_client.get_session(client_id, user_id, channel)
        if not session:
            session = await self.get_session(client_id, user_id, channel)

        session["slots"] = {**session.get("slots", {}), **extracted_slots}
        session["last_activity"] = int(time.time())
        session["turn_count"] = session.get("turn_count", 0) + 1

        await redis_client.save_session(client_id, user_id, channel, session)
        return session

    async def update_intent(
        self,
        client_id: str,
        user_id: str,
        channel: str,
        intent: str,
    ) -> dict:
        """Append intent to history."""
        session = await redis_client.get_session(client_id, user_id, channel)
        if not session:
            session = await self.get_session(client_id, user_id, channel)

        session["intent_history"] = session.get("intent_history", []) + [intent]
        session["last_activity"] = int(time.time())

        await redis_client.save_session(client_id, user_id, channel, session)
        return session

    async def set_async_action(
        self,
        session_id: str,
        action: dict,
    ) -> None:
        """Queue async action (e.g., slow Shopify API)."""
        await redis_client.set_async_action(session_id, action)

    async def get_async_action(self, session_id: str) -> Optional[dict]:
        """Check pending async action."""
        return await redis_client.get_async_action(session_id)

    async def clear_async_action(self, session_id: str) -> None:
        """Clear completed async action."""
        await redis_client.clear_async_action(session_id)

    async def generate_wait_ack(self, session: dict) -> str:
        """Generate 'please wait' acknowledgment during async action."""
        return "I'm checking that for you — just a moment..."


# Singleton
state_manager = StateManager()
