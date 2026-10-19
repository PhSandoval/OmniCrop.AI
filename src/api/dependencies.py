"""
Injeção de dependências para autenticação, multi-tenancy e clientes de dados.
"""
from dataclasses import dataclass
from typing import Optional
from fastapi import Header


DEFAULT_TEST_USER_ID = "00000000-0000-0000-0000-000000000000"


@dataclass
class AuthContext:
    """Contexto de autenticação e identidade do usuário multi-tenant."""
    user_id: str
    access_token: Optional[str] = None
    is_authenticated: bool = False


def get_auth_context(
    authorization: Optional[str] = Header(default=None, description="Header Bearer JWT do Supabase"),
    x_user_id: Optional[str] = Header(default=None, description="Header opcional com o UUID do usuário"),
) -> AuthContext:
    """
    Resolve o contexto de autenticação a partir dos headers HTTP.
    Compatível com RLS do Supabase e modo de teste/desenvolvimento.
    """
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    # Define o user_id: prioriza header explícito, fallback para token ou ID padrão
    resolved_user_id = x_user_id
    if not resolved_user_id:
        if token:
            resolved_user_id = f"user_{token[:8]}"
        else:
            resolved_user_id = DEFAULT_TEST_USER_ID

    is_auth = bool(token or x_user_id)
    return AuthContext(
        user_id=resolved_user_id,
        access_token=token,
        is_authenticated=is_auth,
    )
