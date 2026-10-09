import asyncio
from app.config import config
from app.core.orchestrator import execute_llm_call

async def test():
    content, model, latency, cost, usage = await execute_llm_call(
    model_name=config.yaml.models.high_tier,
    prompt='Say the word verified and nothing else.',
    max_tokens=10,
    )
    print(f'Response: {content.strip()}')
    print(f'Model Used: {model}')
    print(f'Latency: {latency:.2f} ms')
    print(f'Cost USD: ${cost:.6f}')
    print(f'Usage: {usage}')

asyncio.run(test())