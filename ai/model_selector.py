from __future__ import annotations

import re
import time


def _rank(name: str) -> tuple:
    """Prefer stable, fast Gemini models; use available model names dynamically."""
    short = name.rsplit("/", 1)[-1].lower()
    flash = "flash" in short
    preview = any(word in short for word in ("preview", "experimental", "exp"))
    numbers = tuple(int(n) for n in re.findall(r"\d+", short))
    return (not flash, preview, tuple(-n for n in numbers), short)


def list_available_models(client) -> list[str]:
    """List models this API key exposes for generateContent."""
    available = []
    for model in client.models.list():
        name = getattr(model, "name", None)
        actions = getattr(model, "supported_actions", None) or []
        if name and "generateContent" in actions:
            available.append(name.removeprefix("models/"))
    if not available:
        raise RuntimeError("This API key has no Gemini models available for generateContent.")
    return sorted(set(available), key=_rank)


def generate_content_resilient(client, model: str, *, contents, config=None):
    """Retry transient Gemini overloads, then try other exposed models."""
    available = list_available_models(client)
    candidates = [model, *(name for name in available if name != model)]
    transient_codes = {429, 500, 502, 503, 504}
    failures = []

    for candidate in candidates:
        for attempt in range(3):
            try:
                return client.models.generate_content(
                    model=candidate, contents=contents, config=config
                )
            except Exception as exc:
                status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
                message = str(exc).lower()
                try:
                    status_number = int(status)
                except (TypeError, ValueError):
                    status_number = None
                transient = status_number in transient_codes or any(
                    marker in message
                    for marker in ("503", "unavailable", "overloaded", "429", "rate limit", "500", "502", "504")
                )
                failures.append(f"{candidate}: {status or type(exc).__name__}")
                if not transient:
                    raise
                if attempt < 2:
                    time.sleep(2 ** attempt)

    details = "; ".join(failures[-min(len(failures), 8):])
    raise RuntimeError(
        "Gemini is temporarily unavailable across the models exposed to this API key. "
        f"Please retry shortly. Details: {details}"
    )


def select_available_model(client) -> str:
    """Probe accessible Gemini models and return the first one responding now."""
    available = list_available_models(client)

    failures = []
    for name in available:
        try:
            response = client.models.generate_content(
                model=name,
                contents="Reply with the single word OK.",
                config={"max_output_tokens": 4},
            )
            if response is not None:
                return name
            failures.append(f"{name}: empty response")
        except Exception as exc:
            status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            failures.append(f"{name}: {status or type(exc).__name__}")

    details = "; ".join(failures[:5])
    if len(failures) > 5:
        details += f"; and {len(failures) - 5} more"
    raise RuntimeError(
        f"None of the {len(available)} Gemini models available to this API key responded to a quick availability check. "
        f"Please retry shortly. Details: {details}"
    )
