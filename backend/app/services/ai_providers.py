"""AI provider abstraction.

The business logic (ai_service.py) never talks to a vendor API directly —
it calls a provider. Two implementations:

- TemplateProvider: deterministic German text, no API key, no data leaves
  the machine. Default in development.
- AnthropicProvider: uses the Anthropic API when AI_API_KEY is set.
  It only ever receives the aggregated, privacy-filtered payload that
  ai_service builds — never raw journal texts or sensitive flags.
"""

from typing import Protocol

from app.core.config import get_settings


class AIProvider(Protocol):
    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """Return a short German text for the given prompts."""
        ...


class TemplateProvider:
    """Fallback without any external API: echoes structured summaries.

    The "generation" is done by ai_service building a complete template
    text; this provider simply returns the prepared fallback contained in
    the user prompt. Kept as a class so the interface stays identical.
    """

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return user_prompt


class AnthropicProvider:
    """Sends the (already aggregated and filtered) prompt to Claude."""

    def __init__(self, api_key: str):
        import anthropic  # imported lazily so the package is optional

        self._client = anthropic.Anthropic(api_key=api_key)

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        )


def get_provider() -> AIProvider:
    """Pick the provider based on configuration."""
    settings = get_settings()
    if settings.ai_api_key:
        return AnthropicProvider(settings.ai_api_key)
    return TemplateProvider()
