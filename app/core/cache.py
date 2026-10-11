import uuid
import logging
from typing import Optional, Dict, List
import numpy as np
import redis.asyncio as redis
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from app.config import config

logger = logging.getLogger(__name__)

redis_client = redis.Redis(host='redis', port=6379, decode_responses=False)
INDEX_NAME = "prompt_cache_idx"


async def initialize_redis_index():
    try:
        await redis_client.ft(INDEX_NAME).info()
        logger.info("Redis vector index already exists.")
    except Exception:
        logger.info("Creating Redis vector index...")
        schema = (
            VectorField(
                "embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": 3072,
                    "DISTANCE_METRIC": "COSINE"
                }
            ),
            TextField("response"),
            TextField("model_used")
        )
        definition = IndexDefinition(prefix=["cache:"], index_type=IndexType.HASH)
        await redis_client.ft(INDEX_NAME).create_index(fields=schema, definition=definition)
        logger.info("Redis vector index created successfully.")


async def check_cache(embedding: List[float]) -> Optional[Dict[str, str]]:
    if not config.yaml.caching.enabled:
        return None

    vector_bytes = np.array(embedding, dtype=np.float32).tobytes()
    query_str = "*=>[KNN 1 @embedding $vec AS vector_score]"
    
    q = (
        Query(query_str)
        .return_fields("response", "model_used", "vector_score")
        .sort_by("vector_score")
        .dialect(2)
    )
    
    try:
        res = await redis_client.ft(INDEX_NAME).search(q, query_params={"vec": vector_bytes})
        
        if res.docs:
            doc = res.docs[0]
            distance = float(doc.vector_score)
            similarity = 1.0 - distance
            
            if similarity >= config.yaml.caching.similarity_threshold:
                return {
                    "response": doc.response.decode("utf-8") if isinstance(doc.response, bytes) else doc.response,
                    "model_used": doc.model_used.decode("utf-8") if isinstance(doc.model_used, bytes) else doc.model_used
                }
    except Exception as e:
        logger.error(f"Redis search error: {e}")
        
    return None


async def store_in_cache(embedding: List[float], response: str, model_used: str):
    if not config.yaml.caching.enabled:
        return
        
    key = f"cache:{uuid.uuid4()}"
    vector_bytes = np.array(embedding, dtype=np.float32).tobytes()
    
    mapping = {
        "embedding": vector_bytes,
        "response": response,
        "model_used": model_used
    }
    
    try:
        await redis_client.hset(key, mapping=mapping)
        await redis_client.expire(key, config.yaml.caching.ttl_seconds)
    except Exception as e:
        logger.error(f"Redis store error: {e}")