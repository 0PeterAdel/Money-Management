"""
Main FastAPI application for Notification Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routes import send_email, send_sms, send_push

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Notification Service for Email, SMS, and Push Notifications"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(send_email.router, prefix=settings.API_V1_PREFIX, tags=["Email"])
app.include_router(send_sms.router, prefix=settings.API_V1_PREFIX, tags=["SMS"])
app.include_router(send_push.router, prefix=settings.API_V1_PREFIX, tags=["Push Notifications"])


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
