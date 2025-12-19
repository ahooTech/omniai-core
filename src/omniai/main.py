from fastapi import FastAPI
from omniai.core.middleware import TenantValidationMiddleware

app = FastAPI(
    title="OMNIAI Core Platform",
    description="The sovereign foundation for trillion-dollar AI applications.",
    version="0.1.0",
)

# Register middleware early in stack
app.add_middleware(TenantValidationMiddleware)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "omniai-core"}

