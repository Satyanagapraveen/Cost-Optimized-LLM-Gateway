import asyncio
import httpx

async def run_simulation():
    # - "Architect" / "Analyze" triggers the High-Tier model.
    # - Simple questions trigger the Low-Tier model.
    base_prompts = [
        "What is the capital of France?", 
        "Analyze the architecture of a modern microservices system.", 
        "How do you boil an egg?", 
        "Can you architect a highly available database schema?", 
        "What is 2 + 2?"
    ]
    
    # 2. Duplicate them to create 50 requests. 
    # Because they repeat, the first 5 will be Cache Misses, 
    # and the next 45 will be instant Cache Hits!
    prompts = base_prompts * 10 

    print(f"Starting simulation of {len(prompts)} requests...\n")
    
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60.0) as client:
        for i, prompt in enumerate(prompts, 1):
            print(f"[{i}/50] Sending: {prompt[:40]}...")
            
            payload = {
                "prompt": prompt,
                "user_id": "cost_simulator",
                "max_tokens": 150
            }
            
            response = await client.post("/v1/chat/completions", json=payload)
            data = response.json()
            
            hit_status = "HIT" if data.get("cache_hit") else "MISS"
            model = data.get("model_used", "unknown")
            print(f"      -> Cache {hit_status} | Model: {model}\n")
            
            # Tiny pause to not overwhelm the LLM API rate limits on the first 5 misses
            await asyncio.sleep(1)

    print("Simulation Complete! Check your analytics endpoint.")

if __name__ == "__main__":
    asyncio.run(run_simulation())