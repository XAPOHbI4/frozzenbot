"""FastAPI main application."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.bot.bot import setup_bot, bot, dp


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events."""
    # Startup
    await setup_bot()

    # Start notification scheduler
    from app.utils.scheduler import start_scheduler
    await start_scheduler()

    # Start bot polling in background
    bot_task = asyncio.create_task(dp.start_polling(bot))

    yield

    # Shutdown
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass
    await bot.session.close()

    # Stop scheduler
    from app.utils.scheduler import stop_scheduler
    await stop_scheduler()


# Create FastAPI app
app = FastAPI(
    title="FrozenFoodBot API",
    description="API for frozen food Telegram bot",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - SECURITY CRITICAL CONFIGURATION
# NEVER use ["*"] for allow_origins in production as it allows any website
# to make requests to your API, potentially leading to data theft and CSRF attacks
app.add_middleware(
    CORSMiddleware,
    # Secure origins - only allow specific domains
    # For development: localhost and common dev ports
    # For production: replace with your actual domain(s)
    allow_origins=[
        "http://localhost:3000",    # React dev server default
        "http://localhost:5173",    # Vite dev server default
        "http://localhost:8080",    # Alternative dev port
        "http://127.0.0.1:3000",   # Alternative localhost format
        # Production domains
        "https://domashniystandart.com",
        "https://www.domashniystandart.com",
    ],
    # Only allow credentials with specific origins (never with "*")
    allow_credentials=True,
    # Restrict methods to only what's needed
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    # Restrict headers to common ones needed for API requests
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
    ],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "FrozenFoodBot API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Add security middleware
from app.middleware.auth import SecurityHeadersMiddleware, AuditLogMiddleware

app.add_middleware(AuditLogMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Include API routers
from app.api import products, categories, users, orders, admin, payments, notifications, auth

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(orders.router, tags=["orders"])
app.include_router(admin.router, tags=["admin"])
app.include_router(payments.router, tags=["payments"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )