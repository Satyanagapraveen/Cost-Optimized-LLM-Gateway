from fastapi import FastAPI

app=FastAPI(title="Cost Optimized LLM gateway")
@app.get("/health")
def health_check():
    return {"status":"healthy"}
