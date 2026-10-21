import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.ui.components.styles import inject_css
from src.ui.components.header import render_sidebar, render_page_header
from src.data.db import get_user_farms, update_farm, update_farm_boundary, delete_farm, log_audit_event
from src.utils.farm_config import save_config, load_config
from src.data.fetch_api import fetch_farm_data
from src.models.predict import build_payload, get_prediction
from src.utils.geo import (
    create_farm_folium_map,
    ensure_farm_boundary,
    calculate_geodesic_area_ha,
    calculate_perimeter_km,
    generate_parcel_polygon,
)
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Minha Fazenda · OmniCrop AI",
    page_icon="src/ui/assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

if "user" not in st.session_state or not st.session_state["user"]:
    st.session_state["show_landing"] = True
    st.switch_page("app.py")
    st.stop()

# ── 1. Telemetria e Dados para Sidebar ──────────────────────────────
cfg = load_config() or {}
_today_cfg = {}
_resultado_cfg = None
if cfg:
    try:
        _crop_id = cfg.get("crop_id") or "sugarcane"
        _, _today_cfg = fetch_farm_data(cfg["lat"], cfg["lon"], crop_id=_crop_id)
        _payload = build_payload(_today_cfg)
        _resultado_cfg = get_prediction(_payload, crop_id=_crop_id)
    except Exception:
        pass

render_sidebar(_today_cfg, _resultado_cfg)
render_page_header(
    "Minha Fazenda",
    "MOTOR GEOESPACIAL (POSTGIS) · LIMITES TERRITORIAIS E GESTÃO DE TALHÕES",
)

user_id = st.session_state["user"].id
farms = get_user_farms(user_id)

if not farms:
    st.info("Você ainda não possui fazendas cadastradas.")
    if st.button("➕ Cadastrar Novo Talhão (Mapa)", use_container_width=True):
        st.session_state["show_onboarding"] = True
        st.switch_page("app.py")
    st.stop()

# ── 2. Seletor de Talhão Ativo ──────────────────────────────────────
st.markdown(
    '<div class="sec-header">Selecione o Talhão para Inspeção e Manejo</div>',
    unsafe_allow_html=True,
)
farm_names = [f["farm_name"] for f in farms]

active_name = cfg.get("farm_name") if cfg else farm_names[0]
if active_name not in farm_names:
    active_name = farm_names[0]

selected_name = st.selectbox(
    "Talhão Ativo:", farm_names, index=farm_names.index(active_name), label_visibility="collapsed"
)

selected_farm = next(f for f in farms if f["farm_name"] == selected_name)
selected_safe = ensure_farm_boundary(selected_farm)

# ── 3. Motor Geoespacial: Mapa Interativo com Limites PostGIS ────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<div class="sec-header">📍 Mapa Geoespacial de Satélite (Esri World Imagery + PostGIS WGS84)</div>',
    unsafe_allow_html=True,
)

# Constrói o mapa Folium com todas as fazendas e destaque no talhão selecionado
folium_map = create_farm_folium_map(farms, selected_farm_id=selected_farm["id"], height=480)

# OTIMIZAÇÃO CRÍTICA CONTRA LENTIDÃO:
# returned_objects=["last_clicked"] impede que zoom ou pan disparem reruns do Streamlit!
st_folium(
    folium_map,
    height=480,
    use_container_width=True,
    returned_objects=["last_clicked"],
    key="mapa_minha_fazenda",
)

# ── 4. Métricas Geoespaciais do Polígono (Cálculo Geodésico) ─────────
coords = selected_safe.get("boundary_geojson", {}).get("coordinates", [[]])[0]
geo_area = calculate_geodesic_area_ha(coords) if coords else float(selected_farm.get("area_ha", 0))
perimeter = calculate_perimeter_km(coords) if coords else 0.0
num_vertices = len(coords) - 1 if coords else 0

st.markdown("<br>", unsafe_allow_html=True)
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    delta_area = geo_area - float(selected_farm.get("area_ha", 0))
    st.metric(
        "Área Geodésica PostGIS",
        f"{geo_area:.1f} ha",
        delta=f"{delta_area:+.1f} ha vs declarado" if abs(delta_area) > 0.1 else "Equivalente",
        delta_color="off",
        help="Área real calculada sobre a superfície esférica terrestre a partir dos vértices do polígono.",
    )

with col_m2:
    st.metric(
        "Perímetro Territorial",
        f"{perimeter:.2f} km",
        delta="Limites de Cerca",
        delta_color="off",
        help="Comprimento linear total do perímetro do talhão.",
    )

with col_m3:
    st.metric(
        "Vértices do Talhão",
        f"{num_vertices} pontos",
        delta="Polígono Fechado",
        delta_color="off",
        help="Número de vértices de fronteira registrados nas coordenadas WGS84 (EPSG:4326).",
    )

with col_m4:
    st.metric(
        "Centroide de Satélite",
        f"{selected_farm.get('lat', 0):.4f}, {selected_farm.get('lon', 0):.4f}",
        delta=selected_farm.get("city", "SP"),
        delta_color="off",
        help="Ponto geográfico central utilizado para as previsões meteorológicas e de satélite.",
    )

# ── 5. Edição Cadastral e Ajuste de Limites ──────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="sec-header">Identificação do Talhão</div>', unsafe_allow_html=True)
    new_name = st.text_input("Nome do Talhão", value=selected_farm.get("farm_name", ""))
    new_city = st.text_input("Município / Comarca", value=selected_farm.get("city", ""))

    from src.core.crop_config import get_crop_parameters, normalize_crop_id, list_supported_crops

    # Culturas com suporte fisiológico no OmniCrop AI
    supported_crops = list_supported_crops()
    culturas = [c.name for c in supported_crops]
    curr_cult = selected_farm.get("tipo_cultura", "Cana-de-Açúcar")
    if curr_cult not in culturas:
        culturas.append(curr_cult)
    new_cult = st.selectbox(
        "🌾 Cultura Agrícola do Talhão",
        culturas,
        index=culturas.index(curr_cult),
        help="Define os parâmetros biológicos (Temperatura Base para GDA e Kc) e o modelo preditivo associado a este talhão.",
    )

    crop_info = get_crop_parameters(new_cult)
    new_crop_id = crop_info.crop_id

    st.info(
        f"🌱 **Parâmetros Fisiológicos ({crop_info.name}):**\n"
        f"- Temperatura Base de Crescimento (Tb): `{crop_info.base_temp_celsius}°C`\n"
        f"- Coeficiente de Cultura Médio (Kc FAO 56): `{crop_info.kc_default}`\n"
        f"- *{crop_info.description}*"
    )

    st.caption(
        f"📍 **Coordenadas Fixas de Satélite:** Latitude `{selected_farm.get('lat', 0):.6f}` | Longitude `{selected_farm.get('lon', 0):.6f}`"
    )

with col2:
    st.markdown('<div class="sec-header">Parâmetros Agronômicos e Geométricos</div>', unsafe_allow_html=True)
    new_area = st.number_input(
        "Área Cadastrada (hectares)",
        value=float(selected_farm.get("area_ha", 100)),
        min_value=1.0,
        step=5.0,
        help="Altera a área e redimensiona o polígono territorial correspondente.",
    )

    variedades = [
        "RB867515 (Cana)", "CTC9001 (Cana)", "SP803280 (Cana)", "RB966928 (Cana)",
        "TMG 7062 (Soja)", "BMX Potência (Soja)",
        "BRS 1030 (Milho)", "DKB 390 (Milho)",
        "Catuaí Vermelho 144 (Café)", "Mundo Novo IAC 376-4 (Café)",
        "Brachiaria brizantha cv. Marandu (Pecuária)", "Panicum maximum cv. Mombaça (Pecuária)"
    ]
    current_var = selected_farm.get("variedade", "RB867515 (Cana)")
    if current_var not in variedades:
        variedades.append(current_var)
    new_var = st.selectbox("Variedade / Cultivar", variedades, index=variedades.index(current_var))

    orientacao = st.slider(
        "Orientação Territorial (Rotação em Graus)",
        min_value=0,
        max_value=180,
        value=15,
        step=5,
        help="Gira o polígono em torno do centroide para alinhar com o carreador ou relevo real.",
    )

# ── 6. Botões de Ação ────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2, _ = st.columns([1.5, 1, 2])

with col_btn1:
    if st.button("💾 Salvar Alterações e Limites PostGIS", type="primary", use_container_width=True):
        # Regenera o polígono com as novas especificações de área e orientação
        new_poly = generate_parcel_polygon(
            lat=float(selected_farm.get("lat", -21.1704)),
            lon=float(selected_farm.get("lon", -47.8103)),
            area_ha=float(new_area),
            orientation_deg=float(orientacao),
        )

        update_data = {
            "farm_name": new_name,
            "city": new_city,
            "area_ha": new_area,
            "variedade": new_var,
            "tipo_cultura": new_cult,
            "crop_id": new_crop_id,
            "boundary_geojson": new_poly,
        }

        # Atualiza no Supabase com isolamento RLS
        update_farm(selected_farm["id"], user_id, update_data)
        update_farm_boundary(selected_farm["id"], user_id, new_poly)
        try:
            log_audit_event(
                user_id=user_id,
                action="UPDATE_FARM_DATA",
                entity_type="farm",
                entity_id=str(selected_farm["id"]),
                farm_id=str(selected_farm["id"]),
                details={"farm_name": new_name, "area_ha": new_area, "tipo_cultura": new_cult},
                access_token=st.session_state.get('access_token'),
            )
        except Exception:
            pass

        # Atualiza a sessão ativa se a fazenda editada for a atual
        if selected_farm["id"] == cfg.get("id"):
            selected_farm.update(update_data)
            st.session_state["active_farm"] = selected_farm
            save_config(selected_farm)

        st.success("✅ Limites territoriais e dados cadastrais atualizados com sucesso!")
        st.rerun()

with col_btn2:
    if st.button("🗑️ Apagar Fazenda", use_container_width=True):
        if len(farms) == 1:
            st.error("Você não pode apagar sua única fazenda cadastrada.")
        else:
            delete_farm(selected_farm["id"], user_id)
            try:
                log_audit_event(
                    user_id=user_id,
                    action="DELETE_FARM",
                    entity_type="farm",
                    entity_id=str(selected_farm["id"]),
                    farm_id=str(selected_farm["id"]),
                    details={"farm_name": selected_farm.get("farm_name")},
                    access_token=st.session_state.get('access_token'),
                )
            except Exception:
                pass
            if selected_farm["id"] == cfg.get("id"):
                st.session_state["active_farm"] = None
            st.success("Fazenda removida.")
            st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)
if st.button("➕ Adicionar Novo Talhão (Mapear no Satélite)", use_container_width=False):
    st.session_state["show_onboarding"] = True
    st.switch_page("app.py")
