"""
Zenny Core Channel Adapters
Web, WhatsApp, Email, Messenger
"""

from src.channels.web import WebAdapter
from src.channels.whatsapp import WhatsAppAdapter
from src.channels.email import EmailAdapter
from src.channels.messenger import MessengerAdapter

__all__ = ["WebAdapter", "WhatsAppAdapter", "EmailAdapter", "MessengerAdapter"]
