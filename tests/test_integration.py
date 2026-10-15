import httpx
import pytest
import uuid
from app.api.main import app

@pytest.mark.asyncio
async def test_cache_end_to_end():
    async with httpx.AsyncClient(app=app,base_url="http://webserver") as client:
        # We generate a random UUID so the prompt is 100% unique every time the test runs.
        # This guarantees the first request is ALWAYS a cache miss.
        unique_prompt = f"Integration Test {uuid.uuid4().hex}: What is the speed of light?"
        
        payload = {
            "prompt": unique_prompt,
            "user_id": "integration_tester",
            "max_tokens": 50
        }

        # 2. ACT (First Request)
        print("\nSending first request (Should be Cache Miss)...")
        response1 = await client.post("/v1/chat/completions", json=payload)
        data1 = response1.json()

        # 3. ASSERT (First Request)
        assert response1.status_code == 200
        assert data1["cache_hit"] is False  # Must be false

        # 4. ACT (Second Request - Exact same payload)
        print("Sending second request (Should be Cache Hit)...")
        response2 = await client.post("/v1/chat/completions", json=payload)
        data2 = response2.json()

        # 5. ASSERT (Second Request)
        assert response2.status_code == 200
        assert data2["cache_hit"] is True   # Must be true!
        assert data2["response"] == data1["response"] # The text must be identical