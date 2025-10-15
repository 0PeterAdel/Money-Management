"""
Auth service proxy routes
"""
from fastapi import APIRouter, Request, Response
import httpx
import os

router = APIRouter()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001")


@router.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def auth_proxy(path: str, request: Request):
    """Proxy all auth-related requests to auth service"""
    # Only proxy auth-related paths
    auth_paths = ["register", "link-telegram", "users", "groups"]
    
    if not any(auth_path in path for auth_path in auth_paths):
        return {"error": "Not found"}, 404
    
    # Build the target URL
    target_url = f"{AUTH_SERVICE_URL}/api/v1/{path}"
    
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
