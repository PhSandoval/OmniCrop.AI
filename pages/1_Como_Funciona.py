import streamlit as st
from frontend.components.styles import inject_css

# Configuração da Página
st.set_page_config(page_title="Como Funciona | OmniCrop AI", page_icon="🌱", layout="wide")

# Aplica o CSS global e usa o estilo de Landing (sem sidebar)
inject_css(is_login=True)

# Cabeçalho
st.markdown("<h1 style='text-align: center;'>Como Funciona o OmniCrop AI?</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a1a1aa; font-size: 18px;'>A ponte entre a inteligência agronômica de ponta e a gestão diária da sua lavoura.</p>", unsafe_allow_html=True)
st.markdown("---")

# SEÇÃO 1: PARA O USUÁRIO FINAL (LEIGO)
st.subheader("🌱 Para o Produtor: A Jornada da Informação")
st.markdown("Esqueça a complexidade. O nosso sistema foi desenhado para entregar respostas claras em 4 passos simples:")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.info("📍 **1. Mapeamento**\n\nAdicione a sua fazenda com um clique no mapa. O sistema regista as coordenadas e liga-se aos satélites climáticos instantaneamente.")
with col2:
    st.warning("☁️ **2. Leitura de Clima**\n\nO sistema recolhe automaticamente os dados de chuva, temperatura e radiação solar da sua região nos últimos 90 dias.")
with col3:
    st.success("🧠 **3. Análise IA**\n\nO nosso Satélite Virtual calcula o vigor da planta (NDVI) cruzando o clima com a biologia da cultura, mesmo em dias nublados.")
with col4:
    st.error("📊 **4. Decisão**\n\nReceba alertas de risco hídrico, simule cenários de irrigação e descarregue relatórios em PDF prontos para a equipa de campo.")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# SEÇÃO 2: PARA O AVALIADOR TÉCNICO (RECRUTADORES)
st.subheader("⚙️ Para o Avaliador: Por Baixo do Capô (Arquitetura)")
st.markdown("O OmniCrop AI não é apenas um dashboard, é uma arquitetura SaaS Multi-Tenant robusta e orientada a dados.")

with st.expander("🔐 1. Autenticação e Segurança (Supabase)"):
    st.write('''
    - **Multi-Tenant Real:** Autenticação gerida via Supabase GoTrue com emissão de tokens JWT.
    - **Zero-Trust:** As consultas à base de dados passam por políticas de *Row Level Security* (RLS) no PostgreSQL. Um utilizador nunca tem acesso aos talhões de outro, mesmo ao nível do motor da base de dados.
    ''')

with st.expander("🤖 2. Machine Learning Preditivo (XGBoost)"):
    st.write('''
    - **O Problema:** Satélites óticos (como o Sentinel-2) ficam "cegos" com a cobertura de nuvens típica do clima tropical.
    - **A Solução:** Treinámos um modelo *Gradient Boosting* (XGBoost) que utiliza dados meteorológicos contínuos (Open-Meteo) para inferir o NDVI atual, garantindo 100% de visibilidade diária.
    - **Roteamento de Domínio:** O sistema possui uma arquitetura modular preparada para carregar modelos específicos consoante o `tipo_cultura` (Cana, Soja, Café).
    ''')

with st.expander("📄 3. Inteligência Artificial Generativa (Google Gemini)"):
    st.write('''
    - Integração com a API do Google Gemini (LLM) utilizando a técnica de *Retrieval-Augmented Generation* (RAG) leve.
    - A IA consome os KPIs meteorológicos calculados no backend e redige um parecer agronómico autónomo, que é compilado dinamicamente num documento PDF (via `fpdf2`) para partilha imediata.
    ''')

with st.expander("🌐 4. Stack Tecnológico (Frontend & Backend)"):
    st.write('''
    - **Frontend:** Desenvolvido integralmente em Python com Streamlit, utilizando injeção de CSS customizado (*Glassmorphism*) e manipulação de estado (`session_state`) para sessões assíncronas.
    - **Visualização de Dados:** Gráficos interativos renderizados com Plotly e mapas georreferenciados com Folium/Leaflet.
    ''')

st.markdown("<br>", unsafe_allow_html=True)

# CTA Final
col_cta1, col_cta2, col_cta3 = st.columns([1, 2, 1])
with col_cta2:
    st.markdown("<p style='text-align: center;'>Pronto para ver o sistema em ação?</p>", unsafe_allow_html=True)
    if st.button("🚀 Voltar e Aceder à Plataforma", use_container_width=True, type="primary"):
        st.switch_page("app.py")
