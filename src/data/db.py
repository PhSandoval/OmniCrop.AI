import os
import streamlit as st
from supabase import create_client, Client

def _get_credential(key: str, default: str = "") -> str:
    """Busca credenciais por variável de ambiente ou st.secrets de forma segura para CI/CD."""
    env_val = os.environ.get(key)
    if env_val:
        return env_val
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

def get_supabase(access_token=None) -> Client:
    """
    Retorna cliente Supabase com isolamento de sessão por usuário.
    Injeta o token JWT no cabeçalho PostgREST para fazer valer o Row Level Security (RLS) no PostgreSQL.
    """
    url = _get_credential("SUPABASE_URL", "https://placeholder.supabase.co")
    key = _get_credential("SUPABASE_KEY", "placeholder-key")
    client = create_client(url, key)
    
    token = access_token
    if not token:
        try:
            token = st.session_state.get('access_token')
        except Exception:
            token = None

    if token:
        client.postgrest.auth(token)
        
    return client

def login_user(email, password):
    supabase = get_supabase()
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def register_user(email, password):
    supabase = get_supabase()
    return supabase.auth.sign_up({"email": email, "password": password})

def get_user_farms(user_id, access_token=None):
    supabase = get_supabase(access_token)
    res = supabase.table("fazendas").select("*").eq("user_id", user_id).order("farm_name").execute()
    farms = res.data if hasattr(res, "data") and res.data is not None else []
    
    # Normalização de crop_id em todas as fazendas carregadas
    from src.core.crop_config import normalize_crop_id
    for f in farms:
        if not f.get("crop_id"):
            f["crop_id"] = normalize_crop_id(f.get("tipo_cultura", "sugarcane"))

    try:
        from src.utils.geo import ensure_farm_boundary
        return [ensure_farm_boundary(f) for f in farms]
    except Exception:
        return farms

def insert_farm(user_id, farm_name, city, lat, lon, tipo_cultura="Cana-de-Açúcar", area_ha=100, boundary_geojson=None, access_token=None, crop_id=None):
    supabase = get_supabase(access_token)
    from src.core.crop_config import normalize_crop_id
    resolved_crop_id = crop_id or normalize_crop_id(tipo_cultura)

    if boundary_geojson is None:
        try:
            from src.utils.geo import generate_parcel_polygon
            boundary_geojson = generate_parcel_polygon(lat, lon, area_ha)
        except Exception:
            boundary_geojson = None

    data = {
        "user_id": user_id,
        "farm_name": farm_name,
        "city": city,
        "lat": lat,
        "lon": lon,
        "boundary_geojson": boundary_geojson,
        "variedade": "RB867515",
        "area_ha": area_ha,
        "alert_amarelo": 0.6,
        "alert_vermelho": 0.4,
        "chuva_critica": 30,
        "gda_critico": 150,
        "tipo_cultura": tipo_cultura,
        "crop_id": resolved_crop_id
    }
    return supabase.table("fazendas").insert(data).execute()

def update_farm_boundary(farm_id, user_id, boundary_geojson, access_token=None):
    supabase = get_supabase(access_token)
    return supabase.table("fazendas").update({"boundary_geojson": boundary_geojson}).eq("id", farm_id).eq("user_id", user_id).execute()

def update_farm(farm_id, user_id, update_data, access_token=None):
    supabase = get_supabase(access_token)
    payload = dict(update_data)
    if "tipo_cultura" in payload and "crop_id" not in payload:
        from src.core.crop_config import normalize_crop_id
        payload["crop_id"] = normalize_crop_id(payload["tipo_cultura"])
    return supabase.table("fazendas").update(payload).eq("id", farm_id).eq("user_id", user_id).execute()

def delete_farm(farm_id, user_id, access_token=None):
    supabase = get_supabase(access_token)
    return supabase.table("fazendas").delete().eq("id", farm_id).eq("user_id", user_id).execute()

# ── CAMADA OURO MULTI-TENANT (SUPABASE POSTGRESQL + RLS) ──────────────

def insert_farm_gold_kpis(farm_id: str, kpis_data: dict, access_token=None):
    """
    Insere resumo executivo da Camada Ouro associado à fazenda no Supabase.
    Protegido por RLS: O PostgreSQL valida que farm_id pertence ao auth.uid() do access_token.
    """
    supabase = get_supabase(access_token)
    payload = dict(kpis_data)
    payload["farm_id"] = str(farm_id)
    payload.pop("id", None)
    return supabase.table("kpis_gold").insert(payload).execute()

def get_farm_gold_kpis(farm_id: str, limit: int = 15, access_token=None) -> list[dict]:
    """
    Consulta o histórico executivo da Camada Ouro para o talhão.
    Protegido por RLS: A Fazenda A NUNCA receberá dados da Fazenda B.
    """
    supabase = get_supabase(access_token)
    res = (
        supabase.table("kpis_gold")
        .select("*")
        .eq("farm_id", str(farm_id))
        .order("processed_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data if hasattr(res, "data") and res.data is not None else []

def get_latest_farm_gold_kpi(farm_id: str, access_token=None) -> dict | None:
    """
    Retorna o KPI executivo mais recente da Camada Ouro para o talhão selecionado.
    """
    records = get_farm_gold_kpis(farm_id, limit=1, access_token=access_token)
    return records[0] if records else None


# ── AUDITORIA LGPD E GOVERNANÇA (SUPABASE POSTGRESQL + RLS) ───────────

def log_audit_event(
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    farm_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    trace_id: str | None = None,
    access_token: str | None = None,
) -> dict:
    """
    Registra um evento de auditoria imutável (LGPD e Governança) no Supabase PostgreSQL.
    """
    supabase = get_supabase(access_token)
    payload = {
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
        "farm_id": str(farm_id) if farm_id else None,
        "details": details or {},
        "ip_address": ip_address,
        "trace_id": trace_id,
    }
    return supabase.table("audit_logs").insert(payload).execute()


def get_audit_logs(user_id: str, limit: int = 50, access_token: str | None = None) -> list[dict]:
    """
    Consulta os logs de auditoria do usuário ativo.
    Protegido por RLS no PostgreSQL.
    """
    supabase = get_supabase(access_token)
    res = (
        supabase.table("audit_logs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data if hasattr(res, "data") and res.data is not None else []
