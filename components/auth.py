import streamlit as st
from components.db import login_user, register_user
from streamlit_cookies_controller import CookieController

def render_auth_page():
    import base64
    with open("assets/logo.png", "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode()

    col1, col2, col3 = st.columns([1, 2, 1])


    with col2:
        # Logo + nome + subtítulo — tudo dentro da coluna central
        st.markdown(f"""
        <div style="display:flex; flex-direction:column; align-items:center;
                    text-align:center; margin-bottom:18px;">
            <img src="data:image/png;base64,{_logo_b64}"
                 style="width:170px; height:170px; object-fit:contain;
                        border-radius:50%; margin-bottom:10px;">
            <h1 style="color:#ffffff; font-size:30px; font-weight:800;
                       letter-spacing:-0.02em; margin:0 0 4px 0;
                       text-shadow:0 2px 12px rgba(0,0,0,0.55);">
                OmniCrop AI
            </h1>
            <p style="color:rgba(200,210,200,0.85); font-size:14px; margin:0;">
                SaaS de Inteligência Agronômica
            </p>
        </div>
        """, unsafe_allow_html=True)


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
