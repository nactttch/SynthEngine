"""Base class for all SynthEngine agents."""
import json
import os
import anthropic

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


class BaseAgent:
    role: str = ""

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model

    def call(self, prompt: str, context: dict = None, max_tokens: int = 8192) -> dict:
        content = prompt
        if context:
            content = f"<context>\n{json.dumps(context, indent=2)}\n</context>\n\n{prompt}"

        response = get_client().messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=self.role,
            messages=[{"role": "user", "content": content}],
        )

        return self._parse(response.content[0].text)

    def _parse(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # strip opening fence + optional language tag, and closing fence
            start = 1 if lines[0].startswith("```") else 0
            end   = -1 if lines[-1].strip() == "```" else len(lines)
            text  = "\n".join(lines[start:end])
        return json.loads(text)
