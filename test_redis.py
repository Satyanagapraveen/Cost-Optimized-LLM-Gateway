import asyncio
import numpy as np
from app.core.cache import initialize_redis_index, store_in_cache, check_cache

async def test():
    # 1. Initialize Index
    print('Initializing Index...')
    await initialize_redis_index()

    # 2. Create mock 3072D vector (representing 'What is AI?')
    mock_vector = np.random.rand(3072).tolist()

    # 3. Store in cache
    print('Storing mock vector in cache...')
    await store_in_cache(mock_vector, 'AI is Artificial Intelligence', 'gemini/mock')

    # 4. Search for exact same vector (Should be Similarity ~ 1.0)
    print('Searching cache...')
    result = await check_cache(mock_vector)

    if result:
        print(f"Cache Hit! Response: {result['response']}")
    else:
        print('Cache Miss!')
asyncio.run(test())