"""
Zendesk Integration
Ticket creation, user lookup.
"""

from typing import Optional
import httpx
import base64


class ZendeskClient:
    """Zendesk API v2 client."""

    def __init__(self, subdomain: str, api_token: str, email: str = "api@zeromanual.com"):
        self.subdomain = subdomain
        self.base_url = f"https://{subdomain}.zendesk.com/api/v2"
        # Zendesk auth: email/token:api_token
        credentials = base64.b64encode(f"{email}/token:{api_token}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        }

    async def create_ticket(
        self,
        subject: str,
        body: str,
        requester_email: str,
        priority: str = "normal",
        tags: Optional[list] = None,
    ):
        """Create a support ticket."""
        url = f"{self.base_url}/tickets.json"
        data = {
            "ticket": {
                "subject": subject,
                "comment": {"body": body},
                "requester": {"email": requester_email},
                "priority": priority,
                "tags": tags or ["zenny", "escalation"],
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=data, timeout=10.0)
            response.raise_for_status()
            return response.json()

    async def get_user(self, email: str):
        """Get user by email."""
        url = f"{self.base_url}/users/search.json"
        params = {"query": f"email:{email}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params, timeout=10.0)
            response.raise_for_status()
            users = response.json().get("users", [])
            return users[0] if users else None

    async def add_comment(self, ticket_id: int, body: str, public: bool = False):
        """Add internal or public comment to ticket."""
        url = f"{self.base_url}/tickets/{ticket_id}.json"
        data = {
            "ticket": {
                "comment": {
                    "body": body,
                    "public": public,
                }
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=self.headers, json=data, timeout=10.0)
            response.raise_for_status()
            return response.json()


def get_zendesk_client(subdomain: str, api_token: str, email: Optional[str] = None) -> ZendeskClient:
    """Factory function."""
    return ZendeskClient(subdomain, api_token, email or "api@zeromanual.com")
