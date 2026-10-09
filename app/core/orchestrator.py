import logging
import time
import litellm
from typing import Any, Dict, Optional, Tuple
from litellm import acompletion
from litellm.exceptions import APIConnectionError, RateLimitError
from app.config import config

logger = logging.getLogger(__name__)


def get_fallback_model(primary_model: str) -> Optional[str]:
    for fallback in config.yaml.fallbacks:
        if fallback.primary == primary_model:
            return fallback.backup
    return None


async def execute_llm_call(model_name: str, prompt: str, max_tokens: int = 500) -> Tuple[str, str, float, float, Dict[str, int]]:
    messages = [{"role": "user", "content": prompt}]
    start_time = time.perf_counter()

    try:
        response = await acompletion(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens
        )
        model_used = model_name
    except (RateLimitError, APIConnectionError) as error:
        fallback_model = get_fallback_model(model_name)
        if not fallback_model:
            raise error

        logger.warning(f"Primary model {model_name} failed with {type(error).__name__}. Retrying with fallback model {fallback_model}.")
        response = await acompletion(
            model=fallback_model,
            messages=messages,
            max_tokens=max_tokens
        )
        model_used = fallback_model

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    content = response.choices[0].message.content or ""

    try:
        cost_usd = float(litellm.completion_cost(completion_response=response))
    except Exception:
        cost_usd = 0.0

    usage_data = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens
    }

    return content, model_used, latency_ms, cost_usd, usage_data