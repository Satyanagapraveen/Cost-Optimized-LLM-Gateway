import logging
from typing import Optional, List
from litellm import aembedding
from app.config import config

logger=logging.getLogger(__name__)
async def generate_embedding(text: str)->List[float]:
    model_name=config.yaml.models.embedding
    try:
        response= await aembedding(
            model=model_name,
            input=text
        )
        vector=response.data[0]["embedding"]
        return vector
    except Exception as error:
        logger.error(f"Embedding generation failed for model {model_name}:{error}")
        raise error
    
    
    