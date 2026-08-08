import anthropic

from app.core.config import settings


class AnthropicReplyError(RuntimeError):
    """Raised when the Anthropic API could not produce a reply."""


class AnthropicClient:
    """Isolates the Anthropic SDK from the rest of the application."""

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate_reply(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> str:
        try:
            async with self._client.messages.stream(
                model=settings.anthropic_model,
                max_tokens=4096,
                system=system_prompt,
                thinking={"type": "adaptive"},
                messages=messages,
            ) as stream:
                response = await stream.get_final_message()
        except Exception as exc:
            # Covers anthropic.APIError (rate limits, server errors, refusals)
            # and configuration failures the SDK raises before any request is
            # sent (e.g. a missing ANTHROPIC_API_KEY) -- both are "the
            # copilot is unavailable right now" from the caller's view.
            raise AnthropicReplyError(str(exc)) from exc

        return "".join(block.text for block in response.content if block.type == "text")
