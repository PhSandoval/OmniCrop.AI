# 🌾 SugarCane NDVI Predictor (DSS)

Um Sistema de Suporte à Decisão (DSS) focado na previsão do vigor vegetativo (NDVI) da cana-de-açúcar.
Criado inteiramente como uma **Arquitetura Monolítica no Streamlit**, ideal para deploy em nuvem (SaaS) com foco em AgTech.

## 🏗 Arquitetura

O sistema é dividido em **Ambiente Local (A Fábrica)** e **Ambiente Cloud (O Produto)**.

* `src/`: Scripts de ETL e Treino (Rodam localmente para treinar a IA).
* `app.py`: O Dashboard do usuário final (Streamlit).
* `models/`: O Cérebro da IA exportado (XGBoost/HistGradientBoosting).
* `data/processed/`: O banco de métricas históricas leve.

## 🚀 Como rodar
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
