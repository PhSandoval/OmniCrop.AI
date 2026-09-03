import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.styles import inject_css
from components.farm_config import load_config, is_configured
from components.live_data import fetch_farm_data
from components.api_client import build_payload, get_prediction
from components.header import render_sidebar, render_page_header

import google.generativeai as genai

st.set_page_config(page_title="Copilot IA · SugarCane", layout="wide", initial_sidebar_state="expanded")

if 'user' not in st.session_state or not st.session_state['user']:
    st.info("A sua sessão expirou. Faça login novamente para acessar o sistema.")
    st.page_link("app.py", label="Ir para Login 🔒")
    st.stop()

inject_css()

if not is_configured():
    st.warning("Fazenda não configurada. Conclua o Onboarding primeiro.")
    st.stop()

cfg = load_config()

# Setup Gemini API Key
if "GEMINI_API_KEY" not in st.secrets:
    st.warning("⚠️ Chave GEMINI_API_KEY não encontrada no secrets.toml. O assistente não funcionará.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def render_copilot():
    # 1. Busca dos Dados da Fazenda
    df_live, today = fetch_farm_data(cfg["lat"], cfg["lon"])
    payload = build_payload(today)
    resultado = get_prediction(payload)
    
    render_sidebar(today, resultado)
    render_page_header("Copilot IA", "SEU ASSISTENTE VIRTUAL AGRONÔMICO (RAG)")
    
    # 2. Inicializa histórico de chat
    if 'mensagens_chat' not in st.session_state:
        st.session_state['mensagens_chat'] = []
        
    # 3. Montagem do Contexto Oculto (O Segredo do RAG Context-Aware)
    ndvi = resultado.get("ndvi_previsto", 0)
    chuva = payload.get("chuva_acumulada_30d", 0)
    gda = payload.get("graus_dia_acumulados", 0)
    alertas = resultado.get("fatores_de_risco_identificados", [])
    alertas_str = ", ".join(alertas) if alertas else "Nenhum risco detectado."
    
    contexto_oculto = f"""Você é o SugarCane Copilot, um agrônomo especialista sênior ajudando na gestão de uma fazenda de cana-de-açúcar.
Dados atuais da fazenda '{cfg.get("farm_name", "Desconhecida")}':
- NDVI Previsto: {ndvi:.3f}
- Chuva (últimos 30 dias): {chuva:.1f} mm
- GDA: {gda}
- Alertas de Risco Ativos: {alertas_str}

Responda de forma profissional, direta e concisa. Forneça conselhos práticos de manejo se questionado. Nunca revele que você é uma IA genérica, assuma a persona do SugarCane Copilot."""
    
    try:
        # ATUALIZACAO 2026: Usando o modelo gemini-3.6-flash conforme instruido pela API
        modelo = genai.GenerativeModel('gemini-3.6-flash', system_instruction=contexto_oculto)
        
        # Se a sessao existente for de um modelo antigo (1.5), nos a deletamos
        if 'chat_session' in st.session_state:
            if hasattr(st.session_state['chat_session'], 'model') and '3.6' not in getattr(st.session_state['chat_session'].model, 'model_name', ''):
                del st.session_state['chat_session']
                
        if 'chat_session' not in st.session_state:
            st.session_state['chat_session'] = modelo.start_chat(history=[])
    except Exception as e:
        pass

    # 4. Renderiza histórico na UI
    for msg in st.session_state['mensagens_chat']:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # 5. Input do Usuário
    prompt_usuario = st.chat_input("Pergunte ao seu agrônomo virtual...")
    
    if prompt_usuario:
        with st.chat_message("user"):
            st.markdown(prompt_usuario)
        st.session_state['mensagens_chat'].append({"role": "user", "content": prompt_usuario})
        
        with st.chat_message("assistant"):
            with st.spinner("Analisando dados da fazenda..."):
                try:
                    # In 2026, old session states might hold references to deprecated 1.5 models. 
                    # If we catch an error, we wipe the session state and try again.
                    response = st.session_state['chat_session'].send_message(prompt_usuario)
                    try:
                        resposta_texto = response.text
                    except ValueError:
                        resposta_texto = "Desculpe, o filtro de segurança do Google bloqueou esta resposta. Por favor, reformule sua pergunta para mantê-la no contexto agronômico."
                    st.markdown(resposta_texto)
                    st.session_state['mensagens_chat'].append({"role": "assistant", "content": resposta_texto})
                except Exception as e:
                    if "404" in str(e) or "not found" in str(e).lower():
                        st.warning("🔄 Atualizando sessão de inteligência para o modelo 3.6...")
                        del st.session_state['chat_session']
                        
                        # Re-inicializa
                        modelo = genai.GenerativeModel('gemini-3.6-flash', system_instruction=contexto_oculto)
                        st.session_state['chat_session'] = modelo.start_chat(history=[])
                        
                        # Tenta enviar de novo
                        try:
                            response = st.session_state['chat_session'].send_message(prompt_usuario)
                            try:
                                resposta_texto2 = response.text
                            except ValueError:
                                resposta_texto2 = "Desculpe, o filtro de segurança do Google bloqueou esta resposta. Por favor, reformule sua pergunta para mantê-la no contexto agronômico."
                            st.markdown(resposta_texto2)
                            st.session_state['mensagens_chat'].append({"role": "assistant", "content": resposta_texto2})
                        except Exception as e2:
                            st.error(f"Erro persistente na API do Google: {e2}")
                    else:
                        st.error(f"Erro ao processar: {e}")

render_copilot()
