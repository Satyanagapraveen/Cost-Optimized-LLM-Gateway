import logging
from fastapi import FastAPI
import uuid

from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

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

async def log_telemetry_background(log_data:dict):
     """
    This function runs AFTER the user receives their response.
    It opens its own isolated database session to prevent connection errors.
    """
     try:
         async with AsyncSessionLocal() as db:
             log_entry=RequestLog(**log_data)
             db.add(log_entry)
             await db.commit()
     except Exception as e:
         logger.error(f"Background database logging failed:{e}")
         
@app.post("/v1/chat/completions", response_model=GatewayResponse)
async def chat_completions(request: GatewayRequest, background_tasks: BackgroundTasks):
    try:
        cleaned_prompt, token_count=process_prompt(request.prompt)
        embedding= await generate_embedding(cleaned_prompt)
        cache_result= await check_cache(embedding)
        if cache_result:
            log_data = {
                "user_id": request.user_id,
                "model_used": cache_result["model_used"],
                "prompt_tokens": token_count,
                "completion_tokens": 0,
                "total_tokens": token_count,
                "cost_usd": 0.0,
                "latency_ms": 0.0,
                "is_cache_hit": True,
            }
            # NEW: Queue the database save operation to happen in the background
            background_tasks.add_task(log_telemetry_background, log_data)
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
        log_data = {
            "user_id": request.user_id,
            "model_used": model_used,
            "prompt_tokens": usage["prompt_tokens"],
            "completion_tokens": usage["completion_tokens"],
            "total_tokens": usage["total_tokens"],
            "cost_usd": cost,
            "latency_ms": latency,
            "is_cache_hit": False,
        }
        background_tasks.add_task(log_telemetry_background, log_data)


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

    
@app.get("/v1/analytics/requests/{request_id}")
async def get_request_log(request_id:uuid.UUID):
    async with AsyncSessionLocal() as db:
        # Build the SQL query: SELECT * FROM request_logs WHERE id = request_id
        query = select(RequestLog).where(RequestLog.id == request_id)
        
        # Execute the query and get the result
        result = await db.execute(query)
        
        # scalar_one_or_none() extracts the single row, or returns None if missing
        log = result.scalar_one_or_none()
        if not log:
            raise HTTPException(status_code=404, detail=" Request Log not found")
        
        # Safely convert the SQLAlchemy object into a JSON-friendly dictionary
        return {
        "id": log.id,
        "timestamp": log.timestamp,
        "user_id": log.user_id,
        "model_used": log.model_used,
        "prompt_tokens": log.prompt_tokens,
        "completion_tokens": log.completion_tokens,
        "total_tokens": log.total_tokens,
        "cost_usd": log.cost_usd,
        "latency_ms": log.latency_ms,
        "is_cache_hit": log.is_cache_hit
        }

@app.get("/v1/analytics/summary")
async def get_calculation_summary():
    """Calculate total cost, total requests, and cache hit ratio."""
    async with AsyncSessionLocal() as db:
        
        # 1. Calculate Total Requests: COUNT(id)
        total_req_result = await db.execute(select(func.count(RequestLog.id)))
        total_requests = total_req_result.scalar() or 0

        # 2. Calculate Total Cost: SUM(cost_usd)
        total_cost_result = await db.execute(select(func.sum(RequestLog.cost_usd)))
        total_cost = total_cost_result.scalar() or 0.0

        # 3. Calculate Average Latency: AVG(latency_ms)
        avg_latency_result = await db.execute(select(func.avg(RequestLog.latency_ms)))
        avg_latency = avg_latency_result.scalar() or 0.0

        # 4. Calculate Cache Hit Rate
        # First, count how many requests had is_cache_hit = True
        cache_hits_query = select(func.count(RequestLog.id)).where(RequestLog.is_cache_hit == True)
        cache_hits_result = await db.execute(cache_hits_query)
        cache_hits = cache_hits_result.scalar() or 0

        # Do the math in Python
        hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "total_cost_usd": round(total_cost, 6),
            "total_requests": total_requests,
            "average_latency_ms": round(avg_latency, 2),
            "cache_hit_rate_percentage": round(hit_rate, 2)
        }

