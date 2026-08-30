import anthropic

from app.core.config import reveal, settings

# max_tokens caps thinking and reply text together. This request streams, so a
# larger budget costs nothing extra and keeps long grounded replies from being
# cut off mid-sentence.
MAX_RESPONSE_TOKENS = 64_000


class AnthropicReplyError(RuntimeError):
    """Raised when the Anthropic API could not produce a reply."""


class AnthropicClient:
    """Isolates the Anthropic SDK from the rest of the application."""

    async def generate_reply(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> str:
        try:
            async with anthropic.AsyncAnthropic(
                api_key=reveal(settings.anthropic_api_key)
            ) as client:
                async with client.messages.stream(
                    model=settings.anthropic_model,
                    max_tokens=MAX_RESPONSE_TOKENS,
                    system=system_prompt,
                    thinking={"type": "adaptive"},
                    messages=messages,
                ) as stream:
                    response = await stream.get_final_message()
        except Exception as exc:
            # API, rate-limit, and local configuration errors all mean the
            # copilot is temporarily unavailable from the caller's view.
            raise AnthropicReplyError(str(exc)) from exc

        reply = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        if not reply:
            raise AnthropicReplyError("Claude returned no text response.")
        return reply
