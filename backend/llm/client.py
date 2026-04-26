"""
llm/client.py
──────────────
Multi-provider LLM client with automatic fallback.

smart tier: Groq 70B → Gemini 2.0 Flash
fast tier:  Groq 8B  → Gemini 2.0 Flash
default:    Groq 8B  → Gemini 2.0 Flash
"""
import os, sys
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import get_settings

# ── Provider chains ───────────────────────────────────────────────────
PROVIDER_CHAIN = {
    "smart":   [("groq", "llama-3.3-70b-versatile"), ("gemini", "gemini-2.0-flash")],
    "fast":    [("groq", "llama-3.1-8b-instant"),    ("gemini", "gemini-2.0-flash")],
    "local":   [("groq", "llama-3.1-8b-instant"),    ("gemini", "gemini-2.0-flash")],
    "default": [("groq", "llama-3.1-8b-instant"),    ("gemini", "gemini-2.0-flash")],
}


def _call_groq(system, user, model, temperature, max_tokens, json_mode):
    from groq import Groq
    settings = get_settings()
    client   = Groq(api_key=settings.groq_api_key)
    kwargs   = {
        "model":    model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "temperature": temperature,
        "max_tokens":  max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    logger.debug(f"Groq | model={model} | tokens={resp.usage.total_tokens}")
    return resp.choices[0].message.content.strip()


def _call_gemini(system, user, model_id, temperature, max_tokens, json_mode):
    from google import genai
    from google.genai import types
    settings = get_settings()
    client   = genai.Client(api_key=settings.gemini_api_key)

    cfg = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    if json_mode:
        cfg = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )

    resp = client.models.generate_content(
        model=model_id,
        contents=user,
        config=cfg,
    )
    logger.debug(f"Gemini | model={model_id}")
    return resp.text.strip()


def call_llm(
    system_prompt: str,
    user_prompt:   str,
    temperature:   float = 0.7,
    max_tokens:    int   = 1024,
    json_mode:     bool  = False,
    model:         str   = "default",
) -> str:
    """
    Call LLM with automatic provider fallback.
    model: "smart" | "fast" | "default"
    """
    settings = get_settings()
    chain    = PROVIDER_CHAIN.get(model, PROVIDER_CHAIN["default"])
    errors   = []

    for provider, model_id in chain:
        # Skip unconfigured providers
        if provider == "groq" and not settings.groq_api_key:
            continue
        if provider == "gemini" and not settings.gemini_api_key:
            continue

        try:
            logger.debug(f"Trying {provider} ({model_id})")

            if provider == "groq":
                return _call_groq(
                    system_prompt, user_prompt,
                    model_id, temperature, max_tokens, json_mode
                )
            elif provider == "gemini":
                return _call_gemini(
                    system_prompt, user_prompt,
                    model_id, temperature, max_tokens, json_mode
                )

        except Exception as e:
            err = str(e)[:120]
            errors.append(f"{provider}: {err}")
            if "rate_limit" in err.lower() or "429" in err:
                logger.warning(f"{provider} rate limited — falling back")
            else:
                logger.warning(f"{provider} failed: {err} — trying next")

    raise RuntimeError(
        f"All LLM providers failed for tier '{model}'.\n"
        f"Errors: {'; '.join(errors)}\n"
        f"Fix: Add GROQ_API_KEY and GEMINI_API_KEY to .env"
    )
