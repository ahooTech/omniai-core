from fastapi import FastAPI
from omniai.api.health import router as health_router
from omniai.core.middleware import TenantValidationMiddleware

app = FastAPI(
    title="OMNIAI Core Platform",
    description="The sovereign foundation for trillion-dollar AI applications.",
    version="0.1.0",
)

# Register middleware early in stack
app.add_middleware(TenantValidationMiddleware)

# Register routes AFTER middleware
app.include_router(health_router)
