import pytest
import httpx
from httpx import ASGITransport
from unittest.mock import patch
import litellm
import uuid

from app.api.main import app

@pytest.mark.asyncio
@patch("app.core.orchestrator.acompletion")
async def test_fallback_triggers_on_rate_limit(mock_acompletion):
    
    # 2. ARRANGE: Create fake responses
    # We create a fake successful response for the second attempt (the backup model)
    class FakeUsage:
        prompt_tokens = 10
        completion_tokens = 15
        total_tokens = 25

    class FakeMessage:
        content = "This is a fake backup answer from the fire drill."

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]
        model = "fake-backup-model"
        usage = FakeUsage()
        # Mocking the dictionary behavior LiteLLM uses for costs
        def get(self, key, default=None):
            return 0.0

    # 3. SET THE TRAP: The "side_effect" dictates what the mock does each time it is called.
    # Call 1: Throw a RateLimitError. 
    # Call 2: Return the FakeResponse.
    mock_acompletion.side_effect = [
        litellm.exceptions.RateLimitError(
            message="FAKE FIRE ALARM: Rate limit exceeded!", 
            llm_provider="primary", 
            model="primary-model"
        ),
        FakeResponse()
    ]

    # 4. ACT: Send a request to the API
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        
        # Use a unique prompt so the Cache doesn't intercept it!
        payload = {
            "prompt": f"Unique Fallback Test {uuid.uuid4()}",
            "user_id": "tester",
            "max_tokens": 50
        }
        
        print("\nSending request to Gateway...")
        response = await client.post("/v1/chat/completions", json=payload)
        data = response.json()

        # 5. ASSERT
        # The API should still return 200 OK because the gateway caught the error and used the backup
        assert response.status_code == 200 
        
        # We prove the text came from our fake backup response
        assert data["response"] == "This is a fake backup answer from the fire drill."
        
        # We prove that 'acompletion' was called exactly twice (Primary failed -> Backup succeeded)
        assert mock_acompletion.call_count == 2