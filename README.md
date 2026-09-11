# 🌱 OmniCrop AI

OmniCrop AI é um **Sistema de Suporte à Decisão (DSS)** voltado para a gestão inteligente de culturas agrícolas. Inicialmente focado em Cana-de-Açúcar, o sistema funciona como um agrônomo virtual, ajudando no monitoramento de lavouras e fornecendo recomendações preditivas para operações de campo.

A aplicação consolida dados climáticos em tempo real, modelos de Machine Learning (XGBoost) para estimativa de vigor vegetativo, e Inteligência Artificial Generativa (Google Gemini) para gerar pareceres executivos instantâneos.


## 🌍 Resiliência Climática & Feature Engineering (El Niño)
O OmniCrop AI foi construído para operar sob anomalias climáticas severas. Diferente de modelos tradicionais que dependem de médias históricas (que falham durante quebras de clima), nossa arquitetura de Machine Learning incorpora o **Índice ENSO (Oceanic Niño Index - ONI)** como uma *feature* direta no algoritmo (XGBoost). O cálculo de deltas de anomalias e o rigoroso controle de *Walk-Forward Validation* e RMSE garantem que o produtor receba projeções de quebra de safra validadas mesmo durante os extremos do El Niño e La Niña.

---

## 📚 Documentação

Para manter o repositório organizado, separamos a documentação em dois guias principais:

1. **[Guia do Desenvolvedor (Design.md)](docs/Design.md):** Contém toda a arquitetura, estrutura de pastas, tecnologias utilizadas e detalhes sobre como o modelo de Machine Learning e o banco de dados operam. Use este guia se você for contribuir com código.
2. **[Guia do Usuário (User_Guide.md)](docs/User_Guide.md):** Contém os Casos de Uso (UCs) da plataforma, explicando funcionalidade por funcionalidade o que o usuário final pode fazer dentro do aplicativo.

---

## 🚀 Como Executar o Projeto Localmente

```bash
# 1. Clone o repositório
git clone https://github.com/PhSandoval/OmniCrop.AI.git
cd OmniCrop.AI

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente (Crie o arquivo .streamlit/secrets.toml)
# Adicione: SUPABASE_URL, SUPABASE_KEY, e GEMINI_API_KEY

# 5. Inicie o dashboard
streamlit run frontend/app.py
```
