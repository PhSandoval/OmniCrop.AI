import streamlit as st
import json
from pathlib import Path

# Fallback local para desenvolvimento, mas em producao usa Supabase
CONFIG_PATH = Path(__file__).resolve().parents[1] / "data" / "farm_config.json"

def get_user_farms_db():
    if 'user' in st.session_state:
        try:
            from components.db import get_user_farms
            return get_user_farms(st.session_state['user'].id)
        except:
            pass
    return []

def load_config() -> dict | None:
    # 1. Tenta pegar a ativa da sessao
    if 'active_farm' in st.session_state and st.session_state['active_farm']:
        return st.session_state['active_farm']
        
    # 2. Se logado, tenta pegar do Supabase
    farms = get_user_farms_db()
    if farms and len(farms) > 0:
        st.session_state['active_farm'] = farms[0]
        st.session_state['user_farms'] = farms
        return farms[0]
        
    # 3. Fallback arquivo json legado (remova depois)
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
            
    return None

def save_config(config: dict) -> None:
    # Em um ambiente SaaS real, atualizamos/inserimos no DB
    if 'user' in st.session_state:
        try:
            from components.db import insert_farm
            res = insert_farm(
                user_id=st.session_state['user'].id,
                farm_name=config.get("name", "Nova Fazenda"),
                city="Localização Padrão",
                lat=config["lat"],
                lon=config["lon"]
            )
            # Atualiza sessao
            if res.data:
                # Faz merge com os limites locais (o BD so tem lat/lon/area)
                farm = res.data[0]
                farm.update(config)
                st.session_state['active_farm'] = farm
                st.session_state['user_farms'] = get_user_farms_db()
                return
        except Exception as e:
            st.error(f"Erro ao salvar na nuvem: {e}")

    # Fallback local
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    st.session_state['active_farm'] = config

def is_configured() -> bool:
    return load_config() is not None
