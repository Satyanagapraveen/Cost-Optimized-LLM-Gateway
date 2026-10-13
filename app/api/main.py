import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import GatewayRequest, GatewayResponse
from app.core.preprocessing import process_prompt
from app.core.router import route_prompt
from app.core.orchestrator import execute_llm_call
from app.core.embeddings import generate_embedding
from app.core.cache import initialize_redis_index, check_cache, store_in_cache
from app.db.database import AsyncSessionLocal
from app.db.models import RequestLog

logger=logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app:FastAPI):
    logger.info("Starting up Gateway...Initializing Redis Index")
    await initialize_redis_index()
    yield
    logger.info("Shutting down gateway.")

app=FastAPI(title="Cost Optimized LLM gateway", lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status":"healthy"}

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.post("/v1/chat/completions", response_model=GatewayResponse)
async def chat_completions(request: GatewayRequest, db:AsyncSession=Depends(get_db)):
    try:
        cleaned_prompt, token_count=process_prompt(request.prompt)
        embedding= await generate_embedding(cleaned_prompt)
        cache_result= await check_cache(embedding)
        if cache_result:
            log_entry=RequestLog(
                user_id=request.user_id,
                    model_used=cache_result["model_used"],
                    prompt_tokens=token_count,
                    completion_tokens=0,
                    total_tokens=token_count,
                    cost_usd=0.0,
                    latency_ms=0.0,
                    is_cache_hit=True
                )
            db.add(log_entry)
            await db.commit()
            return GatewayResponse(
                    model_used=cache_result["model_used"],
                    response=cache_result["response"],
                    cost_usd=0.0,
                    cache_hit=True
                )
        target_model=route_prompt(cleaned_prompt, token_count)

        response_text, model_used, latency, cost, usage = await execute_llm_call(
                model_name=target_model,
                prompt=cleaned_prompt,
                max_tokens=request.max_tokens
            )
        
            # Phase 4.3: Save this new, expensive answer to Redis for the next user
        await store_in_cache(embedding, response_text, model_used)

            # Phase 5.1: Save the Telemetry to PostgreSQL
        log_entry = RequestLog(
            user_id=request.user_id,
            model_used=model_used,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            total_tokens=usage["total_tokens"],
            cost_usd=cost,
            latency_ms=latency,
            is_cache_hit=False
        )
        db.add(log_entry)
        await db.commit()

            # Return the final response to the user
        return GatewayResponse(
            model_used=model_used,
            response=response_text,
            cost_usd=cost,
            cache_hit=False
        )

    except Exception as e:
        logger.error(f"Gateway Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Gateway Error")

    




