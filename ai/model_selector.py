from __future__ import annotations

import re


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
