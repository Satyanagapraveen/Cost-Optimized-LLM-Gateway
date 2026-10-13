import asyncio
from app.db.database import engine, Base
from app.db.models import RequestLog

async def init_db():
    print('Connecting to database...')
    async with engine.begin() as conn:
        print('Executing table creation...')
        await conn.run_sync(Base.metadata.create_all)
    
    print('Success! The request_logs table has been created in PostgreSQL.')
    await engine.dispose()

asyncio.run(init_db())