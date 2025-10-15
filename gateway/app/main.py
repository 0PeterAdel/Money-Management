"""
API Gateway - Main entry point for all microservices
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (2 levels up from this file)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="API Gateway",
    version="1.0.0",
    description="API Gateway for Money Management Microservices"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs (defaults for local development)
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8002")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "status": "running",
        "services": {
            "auth": AUTH_SERVICE_URL,
            "notification": NOTIFICATION_SERVICE_URL
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Proxy auth service routes
@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_proxy(path: str, request: Request):
    """Main gateway proxy - routes requests to appropriate services"""
    
    # Determine which service to route to based on path
    if any(x in path for x in ["register", "link-telegram", "users", "groups"]):
        target_url = f"{AUTH_SERVICE_URL}/api/v1/{path}"
    elif any(x in path for x in ["send-email", "send-sms", "send-push"]):
        target_url = f"{NOTIFICATION_SERVICE_URL}/api/v1/{path}"
    else:
        # Handle main.py routes from original monolith
        # For now, return not found
        return JSONResponse(
            status_code=404,
            content={"detail": "Route not found or not yet migrated"}
        )
    
    # Get request body
    try:
        body = await request.body()
    except:
        body = b""
    
    # Forward the request
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=dict(request.query_params),
                headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
                content=body
            )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
    except httpx.RequestError as e:
        return JSONResponse(
            status_code=503,
            content={"detail": f"Service unavailable: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal error: {str(e)}"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
