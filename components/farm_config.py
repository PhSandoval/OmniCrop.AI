import streamlit as st
import json
from pathlib import Path

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
    if 'active_farm' in st.session_state and st.session_state['active_farm']:
        return st.session_state['active_farm']
        
    farms = get_user_farms_db()
    
    # --- AUTO-CLEANUP FIX ---
    # Remove as fazendas "Nova Fazenda" que foram criadas acidentalmente pelo bug anterior
    if not st.session_state.get('cleaned_up_nova_fazenda') and 'user' in st.session_state:
        deleted_any = False
        for f in farms:
            if f.get("farm_name") == "Nova Fazenda":
                try:
                    from components.db import delete_farm
                    delete_farm(f["id"], st.session_state['user'].id)
                    deleted_any = True
                except:
                    pass
        st.session_state['cleaned_up_nova_fazenda'] = True
        if deleted_any:
            farms = get_user_farms_db() # re-fetch after cleaning
    # ------------------------

    if farms and len(farms) > 0:
        st.session_state['active_farm'] = farms[0]
        st.session_state['user_farms'] = farms
        return farms[0]
        
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
            
    return None

def save_config(config: dict) -> None:
    if 'user' in st.session_state:
        try:
            from components.db import insert_farm, update_farm
            user_id = st.session_state['user'].id
            
            # Se ja tem uma fazenda ativa, so atualiza as configs dela
            if 'active_farm' in st.session_state and st.session_state['active_farm'] and 'id' in st.session_state['active_farm']:
                farm_id = st.session_state['active_farm']['id']
                
                # Prepara dicionario so com as colunas que podem ser atualizadas
                update_data = {}
                if 'area_ha' in config: update_data['area_ha'] = config['area_ha']
                if 'variedade' in config: update_data['variedade'] = config['variedade']
                if 'ndvi_medio_lim' in config: update_data['alert_amarelo'] = config['ndvi_medio_lim']
                if 'ndvi_critico_lim' in config: update_data['alert_vermelho'] = config['ndvi_critico_lim']
                if 'deficit_lim' in config: update_data['chuva_critica'] = abs(config['deficit_lim'])
                if 'dias_calor_lim' in config: update_data['gda_critico'] = config['dias_calor_lim'] * 10 # aprox
                
                # We can't insert 'receber_alertas' because it doesn't exist in Supabase schema yet.
                # So we just ignore it for the DB or handle it separately if we had the column.
                
                res = update_farm(farm_id, user_id, update_data)
                
                # Merge local state
                farm = st.session_state['active_farm']
                farm.update(config)
                st.session_state['active_farm'] = farm
                st.session_state['user_farms'] = get_user_farms_db()
                return
            else:
                # Criando pela primeira vez (Ex: app.py Onboarding)
                res = insert_farm(
                    user_id=user_id,
                    farm_name=config.get("farm_name", "Nova Fazenda"),
                    city=config.get("city", "Localização Desconhecida"),
                    lat=config["lat"],
                    lon=config["lon"]
                )
                if res.data:
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
    
    if 'active_farm' in st.session_state and st.session_state['active_farm']:
        st.session_state['active_farm'].update(config)
    else:
        st.session_state['active_farm'] = config

def is_configured() -> bool:
    return load_config() is not None
