import os

from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# LLM CONFIGURATION
# =========================================================

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "mock",
)

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "",
)

LLM_API_KEY = os.getenv(
    "LLM_API_KEY",
    "",
)


# =========================================================
# INTERVIEW SETTINGS
# =========================================================

LLM_TEMPERATURE = float(
    os.getenv(
        "LLM_TEMPERATURE",
        "0.7",
    )
)

LLM_MAX_TOKENS = int(
    os.getenv(
        "LLM_MAX_TOKENS",
        "500",
    )
)
# =========================================================
# GEMINI FALLBACK CONFIGURATION
# =========================================================

LLM_FALLBACK_MODEL = os.getenv(
    "LLM_FALLBACK_MODEL",
    "",
)

LLM_MAX_RETRIES = int(
    os.getenv(
        "LLM_MAX_RETRIES",
        "2",
    )
)

# =========================================================
# CONFIGURATION VALIDATION
# =========================================================

def get_llm_config() -> dict:
    """
    Return the current LLM configuration.

    API keys are intentionally not printed.
    """

    return {
    "provider": LLM_PROVIDER,
    "model": LLM_MODEL,
    "fallback_model": LLM_FALLBACK_MODEL,
    "api_key_configured": bool(
        LLM_API_KEY
    ),
    "temperature": LLM_TEMPERATURE,
    "max_tokens": LLM_MAX_TOKENS,
    "max_retries": LLM_MAX_RETRIES,
}

def validate_llm_config() -> bool:
    """
    Validate configuration.

    Mock provider does not require an API key.
    Real providers will require one.
    """

    if LLM_PROVIDER == "mock":
        return True

    if not LLM_API_KEY:
        raise ValueError(
            "LLM_API_KEY is not configured."
        )

    if not LLM_MODEL:
        raise ValueError(
            "LLM_MODEL is not configured."
        )

    return True
