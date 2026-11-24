import os

from dotenv import load_dotenv
import litellm
from litellm import Cache

load_dotenv()

litellm.cache = Cache(type="local")

MODEL_NAME = "gemini/gemini-3.5-flash-lite"

api_keys_string = os.getenv("LLM_API_KEYS", "")

API_KEYS = [
    key.strip()
    for key in api_keys_string.split(",")
    if key.strip()
]


async def generate_response(messages, simulated_failures=None):
    simulated_failures = simulated_failures or {}

    if len(API_KEYS) < 2:
        raise RuntimeError("At least 2 LLM API keys must be configured")

    last_error = None

    for index, api_key in enumerate(API_KEYS):
        try:
            key_id = f"key_{index + 1}"

            simulated_status = simulated_failures.get(
                key_id,
                simulated_failures.get("*")
            )

            if simulated_status is not None:
                # Pretend this key failed without calling the real provider
                continue

            response = await litellm.acompletion(
                model=MODEL_NAME,
                messages=messages,
                api_key=api_key,
                caching=True
            )

            hidden_params = getattr(
                response,
                "_hidden_params",
                {}
            ) or {}

            cache_hit = hidden_params.get("cache_hit", False)

            return {
                "response": response,
                "key_id": None if cache_hit else key_id,
                "fallback_attempts": 0 if cache_hit else index,
                "cache_hit": cache_hit
            }

        except (
            litellm.RateLimitError,
            litellm.ServiceUnavailableError,
            litellm.InternalServerError,
            litellm.APIConnectionError
        ) as error:
            last_error = error
            continue

    raise last_error


def parse_simulated_failures(header_value):
    failures = {}

    if not header_value:
        return failures

    for item in header_value.split(","):
        item = item.strip()

        if "=" not in item:
            continue

        key_id, status = item.split("=", 1)

        key_id = key_id.strip()
        status = status.strip()

        if status in {"429", "500", "502", "503"}:
            failures[key_id] = int(status)

    return failures