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
inject_css()

if 'user' not in st.session_state or not st.session_state['user']:
    st.info("A sua sessão expirou. Faça login novamente para acessar o sistema.")
    st.page_link("app.py", label="Ir para Login 🔒")
    st.stop()


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
    
    # Setup history injection for backward compatibility with gemini-pro if flash fails
    history_setup = [
        {"role": "user", "parts": [f"INSTRUÇÃO DO SISTEMA: {contexto_oculto}\n\nConfirme que entendeu."]},
        {"role": "model", "parts": ["Entendido. Eu sou o SugarCane Copilot, utilizarei os dados fornecidos para guiar minhas respostas."]}
    ]

    try:
        # Primeiro tentamos o modelo 1.5 Flash (recomendado)
        modelo = genai.GenerativeModel('gemini-1.5-flash', system_instruction=contexto_oculto)
        if 'chat_session' not in st.session_state:
            st.session_state['chat_session'] = modelo.start_chat(history=[])
    except:
        pass # Ignora erros de build inicial


    # 4. Renderiza histórico na UI
    for msg in st.session_state['mensagens_chat']:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # 5. Input do Usuário
    prompt_usuario = st.chat_input("Pergunte ao seu agrônomo virtual...")
    
    if prompt_usuario:
        # Exibe mensagem do usuário
        with st.chat_message("user"):
            st.markdown(prompt_usuario)
        st.session_state['mensagens_chat'].append({"role": "user", "content": prompt_usuario})
        
        # Chama a API do Gemini com Fallback
        with st.chat_message("assistant"):
            with st.spinner("Analisando dados da fazenda..."):
                try:
                    # Tenta com a sessao ativa do flash
                    response = st.session_state.get('chat_session').send_message(prompt_usuario)
                    st.markdown(response.text)
                    st.session_state['mensagens_chat'].append({"role": "assistant", "content": response.text})
                except Exception as e:
                    if "404" in str(e):
                        # Fallback para o modelo gemini-pro legado
                        try:
                            fallback_model = genai.GenerativeModel('gemini-pro')
                            if 'fallback_session' not in st.session_state:
                                st.session_state['fallback_session'] = fallback_model.start_chat(history=history_setup)
                            
                            response = st.session_state['fallback_session'].send_message(prompt_usuario)
                            st.markdown(response.text)
                            st.session_state['mensagens_chat'].append({"role": "assistant", "content": response.text})
                        except Exception as inner_e:
                            # Let's dynamically find the first available model!
                            available_models = []
                            try:
                                for m in genai.list_models():
                                    if 'generateContent' in m.supported_generation_methods:
                                        available_models.append(m.name)
                                
                                if available_models:
                                    fallback_dynamic = genai.GenerativeModel(available_models[0])
                                    if 'fallback_dynamic_session' not in st.session_state:
                                        st.session_state['fallback_dynamic_session'] = fallback_dynamic.start_chat(history=history_setup)
                                    response = st.session_state['fallback_dynamic_session'].send_message(prompt_usuario)
                                    st.markdown(response.text)
                                    st.session_state['mensagens_chat'].append({"role": "assistant", "content": response.text})
                                else:
                                    st.error("Nenhum modelo compatível encontrado na sua conta.")
                            except Exception as deepest_e:
                                st.error(f"Erro crônico de API. Modelos disponíveis encontrados: {available_models}. Erro: {deepest_e}")
                    else:
                        st.error(f"Ocorreu um erro ao comunicar com a inteligência: {e}")

render_copilot()
