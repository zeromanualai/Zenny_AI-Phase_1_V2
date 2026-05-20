"""
PII Redactor
Strips sensitive data before LLM calls and before saving transcripts.
Regex-based. Fast. Deterministic.
"""

import re
from typing import Optional


# ── Regex Patterns ──
PATTERNS = {
    "CREDIT_CARD": {
        "pattern": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        "replacement": "[REDACTED_CC]",
    },
    "SSN": {
        "pattern": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "replacement": "[REDACTED_SSN]",
    },
    "PHONE_US": {
        "pattern": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "replacement": "[REDACTED_PHONE]",
    },
    "EMAIL": {
        "pattern": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "replacement": "[REDACTED_EMAIL]",
    },
    "ADDRESS_KEYWORDS": {
        "pattern": re.compile(
            r"\b\d+\s+\w+\s+(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr)\b",
            re.IGNORECASE,
        ),
        "replacement": "[REDACTED_ADDRESS]",
    },
}


class PIIRedactor:
    """Redacts personally identifiable information from text."""

    def redact(self, text: str) -> str:
        """Apply all redaction patterns."""
        if not text:
            return text

        result = text
        for name, config in PATTERNS.items():
            result = config["pattern"].sub(config["replacement"], result)

        return result

    def redact_with_log(self, text: str, context: Optional[dict] = None) -> tuple[str, list[dict]]:
        """
        Redact and return log of what was redacted.
        Returns: (redacted_text, redactions_log)
        """
        if not text:
            return text, []

        result = text
        redactions = []

        for name, config in PATTERNS.items():
            matches = list(config["pattern"].finditer(result))
            for match in matches:
                redactions.append({
                    "type": name,
                    "position": (match.start(), match.end()),
                    "original_length": len(match.group()),
                    "context": context or {},
                })
            result = config["pattern"].sub(config["replacement"], result)

        return result, redactions

    def has_pii(self, text: str) -> bool:
        """Quick check if text contains any PII."""
        if not text:
            return False
        for config in PATTERNS.values():
            if config["pattern"].search(text):
                return True
        return False


# Singleton
pii_redactor = PIIRedactor()
