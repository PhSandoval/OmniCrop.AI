# ==============================================================================
# OmniCrop AI - Production Dockerfile
# Suporta tanto o serviço Headless FastAPI quanto o Dashboard Streamlit
# ==============================================================================
FROM python:3.11-slim

# Variáveis de ambiente de runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Instalação de dependências do sistema necessárias para compilação e libs geoespaciais
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalação das dependências Python com cache isolado
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cópia do código-fonte e modelos pré-treinados
COPY . .

# Exposição das portas:
# 8000: FastAPI REST API
# 8501: Streamlit Frontend
EXPOSE 8000 8501

# Comando padrão de inicialização (Headless FastAPI API)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
