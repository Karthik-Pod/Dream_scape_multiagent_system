"""
llm/client.py
──────────────
Multi-provider LLM client with automatic fallback routing.

Provider hierarchy per agent role:
  "smart"  → Groq (70B) → Gemini Flash → Ollama Mistral
  "fast"   → Gemini Flash → Groq (8B) → Ollama Mistral
  "local"  → Ollama Mistral → Groq (8B)

Patent-worthy design:
  Each agent uses a different LLM provider based on cognitive requirements.
  Automatic fallback ensures the pipeline never stops due to rate limits.

Setup:
  Groq:   GROQ_API_KEY in .env (free, 100K tokens/day)
  Gemini: GEMINI_API_KEY in .env (free, 15 req/min — get at aistudio.google.com)
  Ollama: Install ollama, run: ollama pull mistral (fully local, no limits)
"""
import os, json, time
from loguru import logger

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import get_settings


# ── Provider implementations ──────────────────────────────────────────

def _call_groq(system: str, user: str, model: str, temperature: float,
               max_tokens: int, json_mode: bool) -> str:
    """Groq API — LLaMA models, 100K tokens/day free."""
    from groq import Groq
    settings = get_settings()
    client   = Groq(api_key=settings.groq_api_key)

    kwargs = {
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

    resp  = client.chat.completions.create(**kwargs)
    usage = resp.usage
    logger.debug(f"Groq | model={model} | tokens={usage.total_tokens}")
    return resp.choices[0].message.content.strip()


def _call_gemini(system: str, user: str, temperature: float,
                 max_tokens: int, json_mode: bool) -> str:
    """Google Gemini Flash — free tier, 15 req/min."""
    import google.generativeai as genai
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system,
        generation_config=genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json" if json_mode else "text/plain",
        )
    )
    resp = model.generate_content(user)
    logger.debug("Gemini Flash | tokens used")
    return resp.text.strip()


def _call_ollama(system: str, user: str, temperature: float,
                 json_mode: bool) -> str:
    """Ollama local — Mistral, completely free, no limits."""
    import ollama
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]
    options = {"temperature": temperature}
    if json_mode:
        options["format"] = "json"

    resp = ollama.chat(
        model="mistral",
        messages=messages,
        options=options,
    )
    logger.debug("Ollama Mistral | local inference")
    return resp["message"]["content"].strip()


# ── Provider routing table ────────────────────────────────────────────
# Each tier lists providers in priority order.
# If provider fails (rate limit, not configured), moves to next.

PROVIDER_CHAIN = {
    # Heavy reasoning — Coordinator, Plot, Character
    "smart": [
        ("groq",   "llama-3.3-70b-versatile"),
        ("gemini", None),
        ("ollama", None),
    ],
    # Fast structured — Emotion, Visual, Audio
    "fast": [
        ("gemini", None),
        ("groq",   "llama-3.1-8b-instant"),
        ("ollama", None),
    ],
    # Local only — no API calls
    "local": [
        ("ollama", None),
        ("groq",   "llama-3.1-8b-instant"),
    ],
    # Default fallback
    "default": [
        ("groq",   "llama-3.1-8b-instant"),
        ("gemini", None),
        ("ollama", None),
    ],
}


def call_llm(
    system_prompt: str,
    user_prompt:   str,
    temperature:   float = 0.7,
    max_tokens:    int   = 1024,
    json_mode:     bool  = False,
    model:         str   = "default",
) -> str:
    """
    Multi-provider LLM call with automatic fallback.

    Tries providers in order for the given tier.
    If a provider fails (rate limit, not configured, error),
    automatically falls back to the next provider.

    Args:
        model: "smart" | "fast" | "local" | "default"
    """
    settings = get_settings()
    chain    = PROVIDER_CHAIN.get(model, PROVIDER_CHAIN["default"])
    errors   = []

    for provider, model_id in chain:

        # Skip unconfigured providers
        if provider == "groq" and not settings.groq_api_key:
            logger.debug("Groq not configured — skipping")
            continue
        if provider == "gemini" and not settings.gemini_api_key:
            logger.debug("Gemini not configured — skipping")
            continue
        if provider == "ollama" and not settings.ollama_enabled:
            logger.debug("Ollama not enabled — skipping")
            continue

        try:
            logger.debug(f"Trying provider: {provider}")

            if provider == "groq":
                return _call_groq(
                    system_prompt, user_prompt,
                    model_id, temperature, max_tokens, json_mode
                )
            elif provider == "gemini":
                return _call_gemini(
                    system_prompt, user_prompt,
                    temperature, max_tokens, json_mode
                )
            elif provider == "ollama":
                return _call_ollama(
                    system_prompt, user_prompt,
                    temperature, json_mode
                )

        except Exception as e:
            err_str = str(e)
            errors.append(f"{provider}: {err_str[:100]}")

            # Rate limit — log clearly and try next
            if "rate_limit" in err_str.lower() or "429" in err_str or "quota" in err_str.lower():
                logger.warning(f"{provider} rate limited — falling back to next provider")
            else:
                logger.warning(f"{provider} failed: {err_str[:100]} — trying next provider")

            continue

    # All providers failed
    raise RuntimeError(
        f"All LLM providers failed for tier '{model}'.\n"
        f"Errors: {'; '.join(errors)}\n"
        f"Fix: Check API keys in .env or run 'ollama pull mistral' for local fallback."
    )
