"""Shared access control for personal dashboard and stored capture data."""
import hmac

from fastapi import Header, HTTPException, status

from app.config import settings


def require_dashboard_access(x_dashboard_token: str = Header(default="")) -> None:
    configured = settings.dashboard_access_token
    if configured:
        if not x_dashboard_token or not hmac.compare_digest(x_dashboard_token, configured):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A valid X-Dashboard-Token header is required",
            )
        return

    if settings.app_env.lower() in {"production", "prod"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Set DASHBOARD_ACCESS_TOKEN before exposing dashboard data in production",
        )
