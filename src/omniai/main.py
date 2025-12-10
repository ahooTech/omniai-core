from fastapi import FastAPI

app = FastAPI(
    title="OMNIAI Core Platform",
    description="The sovereign foundation for trillion-dollar AI applications.",
    version="0.1.0",
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "omniai-core"}