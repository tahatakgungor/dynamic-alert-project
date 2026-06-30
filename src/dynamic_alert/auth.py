from dataclasses import dataclass

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from dynamic_alert.database import get_db
from dynamic_alert.models import ApiClient

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(slots=True)
class AuthContext:
    client_id: int
    name: str
    role: str


def get_auth_context(
    api_key: str | None = Security(api_key_header),
    db: Session = Depends(get_db),
) -> AuthContext:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    client = db.query(ApiClient).filter(ApiClient.client_key == api_key, ApiClient.enabled.is_(True)).one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return AuthContext(client_id=client.id, name=client.name, role=client.role)


def require_operator(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if auth.role not in {"operator", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator role required")
    return auth


def require_admin(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if auth.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return auth
