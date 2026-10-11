from app.db.database import engine
import asyncio
from sqlalchemy import text

async def test_db():
    try:
        async with engine.begin() as conn:
            result=await conn.execute(text('SELECT 1'))
            row=result.fetchone()
            print(f"DATABASE Connection Sucess! Result:{row[0]}")
    except Exception as e:
        print(f"Database Connection failed {e}")
    finally:
        await engine.dispose()

asyncio.run(test_db())