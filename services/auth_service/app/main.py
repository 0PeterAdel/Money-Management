"""
Main FastAPI application for Auth Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import engine
from app.db.models.user import Base
from app.api.v1.routes import register, login, users, auth, admin

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Authentication and User Management Service - Enhanced with JWT & OTP"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include enhanced authentication routes
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["🔐 Authentication"])
app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["👑 Admin Panel"])

# Include legacy routes (backward compatibility)
app.include_router(register.router, prefix=settings.API_V1_PREFIX, tags=["Legacy - Registration"])
app.include_router(login.router, prefix=settings.API_V1_PREFIX, tags=["Legacy - Authentication"])
app.include_router(users.router, prefix=settings.API_V1_PREFIX, tags=["Users & Groups"])


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
    uvicorn.run(app, host="0.0.0.0", port=8001)
