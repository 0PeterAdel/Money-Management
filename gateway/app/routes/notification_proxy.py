"""
Notification service proxy routes
"""
from fastapi import APIRouter, Request, Response
import httpx
import os

router = APIRouter()

NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification_service:8002")


@router.api_route("/api/v1/notifications/{path:path}", methods=["GET", "POST"])
async def notification_proxy(path: str, request: Request):
    """Proxy all notification-related requests to notification service"""
    # Build the target URL
    target_url = f"{NOTIFICATION_SERVICE_URL}/api/v1/{path}"
    
    # Get request body
    body = await request.body()
    
    # Forward the request
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            params=request.query_params,
            headers=dict(request.headers),
            content=body,
            timeout=30.0
        )
    
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
