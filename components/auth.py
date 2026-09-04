import streamlit as st
from components.db import login_user, register_user
from streamlit_cookies_controller import CookieController

def render_auth_page():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image("assets/logo.png", width=200)
    st.markdown("<h2 style='text-align: center; color: #aaa; font-size: 16px; margin-top: -15px;'>SaaS de Inteligência Agronômica</h2>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Criar Conta"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("E-mail")
                password = st.text_input("Senha", type="password")
                submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
                
                if submit:
                    try:
                        with st.spinner("Autenticando..."):
                            res = login_user(email, password)
                            st.session_state['user'] = res.user
                            st.session_state['access_token'] = res.session.access_token
                            
                            # Salva nos cookies para persistencia
                            try:
                                controller = CookieController()
                                controller.set('sb-access-token', res.session.access_token, max_age=86400*30)
                                controller.set('sb-refresh-token', res.session.refresh_token, max_age=86400*30)
                            except:
                                pass
                                
                            st.rerun()
                    except Exception as e:
                        st.error(f"Falha no login. Verifique suas credenciais.")
                        
        with tab2:
            with st.form("register_form"):
                email = st.text_input("Novo E-mail")
                password = st.text_input("Nova Senha", type="password")
                submit = st.form_submit_button("Registrar", type="primary", use_container_width=True)
                
                if submit:
                    try:
                        with st.spinner("Criando conta..."):
                            res = register_user(email, password)
                            st.success("Conta criada com sucesso! Por favor, verifique sua caixa de entrada (e spam) e confirme seu e-mail antes de fazer login.")
                    except Exception as e:
                        st.error(f"Falha ao registrar: {e}")
