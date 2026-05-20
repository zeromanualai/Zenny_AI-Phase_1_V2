"""
Prompt Manager
Loads base prompts from YAML files + tenant overrides from Supabase.
Version-controlled, tenant-customizable, A/B-test ready.
"""

import os
import yaml
from string import Template
from typing import Optional

from src.services.db import get_supabase


PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


class PromptManager:
    """
    Manages versioned prompt assets with tenant overrides.

    File structure:
        prompts/
          v1.0/
            ecommerce/
              welcome.yml
              order_status.yml
              ...

    Tenant overrides stored in Supabase prompt_overrides table.
    """

    async def load(
        self,
        version: str,
        prompt_name: str,
        variables: dict,
        client_id: Optional[str] = None,
    ) -> str:
        """
        Load and render a prompt.

        Args:
            version: e.g. "v1.0"
            prompt_name: e.g. "welcome", "order_status"
            variables: dict of {{key}} replacements
            client_id: if provided, apply tenant override
        """
        # 1. Load base prompt from YAML
        base_prompt = self._load_base(version, prompt_name)

        # 2. Apply tenant override if exists
        if client_id:
            override = await self._load_override(client_id, prompt_name, version)
            if override:
                base_prompt = self._apply_override(base_prompt, override)

        # 3. Replace variables
        return self._render(base_prompt, variables)

    def _load_base(self, version: str, prompt_name: str) -> str:
        """Load base prompt from YAML file."""
        path = os.path.join(PROMPTS_DIR, version, "ecommerce", f"{prompt_name}.yml")
        if not os.path.exists(path):
            # Fallback: look in root of version
            path = os.path.join(PROMPTS_DIR, version, f"{prompt_name}.yml")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Prompt not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return data.get("base", "")

    async def _load_override(
        self,
        client_id: str,
        prompt_name: str,
        version: str,
    ) -> Optional[dict]:
        """Fetch tenant override from Supabase."""
        db = get_supabase()
        result = (
            db.table("prompt_overrides")
            .select("*")
            .eq("client_id", client_id)
            .eq("prompt_name", prompt_name)
            .eq("version", version)
            .eq("active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None

    def _apply_override(self, base: str, override: dict) -> str:
        """Merge tenant override into base prompt."""
        override_content = override.get("override_content", "")
        if not override_content:
            return base
        # Simple replacement: tenant override replaces base entirely
        # Future: support partial overrides (merge rules)
        return override_content

    def _render(self, template: str, variables: dict) -> str:
        """Replace {{variable}} placeholders."""
        # Convert nested dicts to flat strings for simple replacement
        flat_vars = {}
        for key, value in variables.items():
            if isinstance(value, dict):
                flat_vars[key] = json.dumps(value, indent=2)
            elif isinstance(value, list):
                flat_vars[key] = "\n".join(str(v) for v in value)
            else:
                flat_vars[key] = str(value) if value is not None else ""

        return Template(template).safe_substitute(flat_vars)


# Singleton
prompt_manager = PromptManager()
