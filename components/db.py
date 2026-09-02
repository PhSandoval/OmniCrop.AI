import streamlit as st
from supabase import create_client, Client

# Removido o @st.cache_resource para garantir isolamento de sessao (Seguranca em Multi-tenant)
def get_supabase(access_token=None) -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    client = create_client(url, key)
    
    # Injeta o token JWT do usuario especifico para respeitar o Row Level Security (RLS)
    if access_token:
        client.postgrest.auth(access_token)
        
    return client

def login_user(email, password):
    supabase = get_supabase()
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def register_user(email, password):
    supabase = get_supabase()
    return supabase.auth.sign_up({"email": email, "password": password})

def get_user_farms(user_id):
    # Pega o token da sessao segura do Streamlit
    access_token = st.session_state.get('access_token')
    supabase = get_supabase(access_token)
    res = supabase.table("fazendas").select("*").eq("user_id", user_id).execute()
    return res.data

def insert_farm(user_id, farm_name, city, lat, lon):
    access_token = st.session_state.get('access_token')
    supabase = get_supabase(access_token)
    data = {
        "user_id": user_id,
        "farm_name": farm_name,
        "city": city,
        "lat": lat,
        "lon": lon,
        "variedade": "RB867515",
        "area_ha": 100,
        "alert_amarelo": 0.6,
        "alert_vermelho": 0.4,
        "chuva_critica": 30,
        "gda_critico": 150
    }
    return supabase.table("fazendas").insert(data).execute()
