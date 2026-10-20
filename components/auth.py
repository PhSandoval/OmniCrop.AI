import re
import streamlit as st
from src.data.db import login_user, register_user
from streamlit_cookies_controller import CookieController
from src.core.logger import logger

# ── Constantes de Validação ───────────────────────────────────────────────
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_MIN_PASSWORD_LENGTH = 8


def _validate_email(email: str) -> str | None:
    """Retorna mensagem de erro se inválido, None se válido."""
    if not email or not email.strip():
        return "O e-mail não pode estar em branco."
    if not _EMAIL_RE.match(email.strip()):
        return "Informe um endereço de e-mail válido (ex: nome@dominio.com)."
    return None


def _validate_password(password: str) -> str | None:
    """Retorna mensagem de erro se inválida, None se válida."""
    if not password:
        return "A senha não pode estar em branco."
    if len(password) < _MIN_PASSWORD_LENGTH:
        return f"A senha deve ter pelo menos {_MIN_PASSWORD_LENGTH} caracteres."
    return None

def render_auth_page():
    import base64
    from pathlib import Path
    
    base_dir = Path(__file__).resolve().parents[1]
    logo_path = base_dir / "assets" / "logo.png"
    
    with open(logo_path, "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode()

    st.markdown("""
    <style>
    .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stMainBlockContainer"] {
        position: relative !important;
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        margin-top: 2rem !important;
        margin-bottom: 2rem !important;
        max-width: 500px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        z-index: 1 !important;
    }
    .block-container::before, [data-testid="stAppViewBlockContainer"]::before, [data-testid="stMainBlockContainer"]::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(10, 25, 15, 0.65) !important;
        border: 1px solid rgba(105, 240, 174, 0.15) !important;
        border-radius: 24px !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        z-index: -1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Logo + nome + subtítulo — centralizado no container
    st.markdown(f"""
    <div style="display:flex; flex-direction:column; align-items:center;
                text-align:center; margin-bottom:18px;">
        <img src="data:image/png;base64,{_logo_b64}"
             style="width:170px; height:170px; object-fit:contain;
                    border-radius:50%; margin-bottom:10px; transform: translateX(-8px);">
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
                # Validação local antes de chamar o Supabase
                email_err = _validate_email(email)
                pass_err = _validate_password(password)
                if email_err:
                    st.error(email_err)
                elif pass_err:
                    st.error(pass_err)
                else:
                    try:
                        with st.spinner("Autenticando..."):
                            res = login_user(email.strip(), password)
                            st.session_state['user'] = res.user
                            st.session_state['access_token'] = res.session.access_token

                            # Salva nos cookies para persistência de sessão
                            try:
                                controller = CookieController()
                                controller.set('sb-access-token', res.session.access_token, max_age=86400 * 30)
                                controller.set('sb-refresh-token', res.session.refresh_token, max_age=86400 * 30)
                            except Exception as cookie_err:
                                logger.warning(
                                    "Falha ao persistir token no cookie após login.",
                                    extra={"extra_data": {"error": str(cookie_err), "user_email": email.strip()}},
                                )

                            st.rerun()
                    except Exception as e:
                        logger.warning(
                            "Tentativa de login falhou.",
                            extra={"extra_data": {"user_email": email.strip(), "error": str(e)}},
                        )
                        st.error("Falha no login. Verifique seu e-mail e senha e tente novamente.")
        
        if st.button("⬅️ Voltar", key="btn_back_login", use_container_width=True):
            st.session_state['show_login'] = False
            st.session_state['show_landing'] = True
            st.rerun()
                    
    with tab2:
        with st.form("register_form"):
            email = st.text_input("Novo E-mail")
            password = st.text_input("Nova Senha", type="password")
            submit = st.form_submit_button("Registrar", type="primary", use_container_width=True)
            
            if submit:
                # Validação local antes de chamar o Supabase
                email_err = _validate_email(email)
                pass_err = _validate_password(password)
                if email_err:
                    st.error(email_err)
                elif pass_err:
                    st.error(pass_err)
                else:
                    try:
                        with st.spinner("Criando conta..."):
                            res = register_user(email.strip(), password)
                            st.success(
                                "Conta criada com sucesso! Verifique sua caixa de entrada "
                                "(e spam) e confirme seu e-mail antes de fazer login."
                            )
                    except Exception as e:
                        logger.warning(
                            "Tentativa de registro falhou.",
                            extra={"extra_data": {"user_email": email.strip(), "error": str(e)}},
                        )
                        st.error("Falha ao criar conta. Verifique se o e-mail já está em uso ou tente novamente.")
        
        if st.button("⬅️ Voltar", key="btn_back_register", use_container_width=True):
            st.session_state['show_login'] = False
            st.session_state['show_landing'] = True
            st.rerun()
