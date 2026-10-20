"""
Módulo de Governança e Model Registry via Hugging Face Hub - OmniCrop AI.
Permite versionamento, publicação e download de modelos preditivos na nuvem
com fallback resiliente e transparente para arquivos locais (.pkl).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from src.core.logger import logger

try:
    from huggingface_hub import HfApi, hf_hub_download
    HF_HUB_AVAILABLE = True
except ImportError:  # pragma: no cover
    HfApi = None  # type: ignore
    hf_hub_download = None  # type: ignore
    HF_HUB_AVAILABLE = False


DEFAULT_HF_REPO_ID = os.getenv("HF_MODEL_REPO_ID", "phsandoval/omnicrop-ndvi-models")


def generate_model_card() -> str:
    """
    Gera o Model Card oficial com metadados do Hugging Face Hub e tabela executiva
    de métricas de validação temporal (2024–2026) das 5 culturas agrícolas suportadas.
    """
    return """---
tags:
  - agtech
  - tabular-regression
  - scikit-learn
  - ndvi
  - omnicrop
library_name: scikit-learn
license: apache-2.0
---

# 🌱 OmniCrop AI — Multi-Crop NDVI Predictive Models

Modelos oficiais de Machine Learning para estimativa de vigor vegetativo (NDVI) e
suporte à decisão agronômica (DSS) desenvolvidos para a plataforma **OmniCrop AI**.

## 🌾 Culturas Monitoradas e Parâmetros Fisiológicos

Os modelos utilizam arquitetura **HistGradientBoostingRegressor** com separação
temporal de safras (Walk-Forward Validation 2024–2026), ingerindo variáveis biofísicas
como Graus-Dia Acumulados ($T_b$) e balanço hídrico derivado de coeficientes FAO-56 ($K_c$).

| Cultura | ID Canônico | $T_b$ (°C) | $K_c$ Médio | MAE | RMSE | $R^2$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Cana-de-Açúcar | `sugarcane` | 18.0 | 1.05 | 0.0217 | 0.0315 | 0.8520 |
| Soja | `soybean` | 10.0 | 1.15 | 0.0557 | 0.1122 | 0.8684 |
| Milho | `corn` | 10.0 | 1.20 | 0.1022 | 0.1460 | 0.7053 |
| Café | `coffee` | 10.0 | 1.05 | 0.0254 | 0.0391 | 0.8801 |
| Pecuária (Pastagem) | `pasture` | 15.0 | 0.90 | 0.0238 | 0.0389 | 0.9674 |

## 📐 Features Utilizadas
- `chuva_acumulada_30d`: Precipitação acumulada nos últimos 30 dias (mm)
- `chuva_acumulada_60d`: Precipitação acumulada nos últimos 60 dias (mm)
- `chuva_acumulada_90d`: Precipitação acumulada nos últimos 90 dias (mm)
- `GDA_mensal`: Graus-Dia Acumulados no mês com corte inferior na temperatura base ($T_b$)
"""


def download_model_from_registry(
    crop_id: str,
    repo_id: str = DEFAULT_HF_REPO_ID,
    local_dir: str = "src/models",
) -> str:
    """
    Tenta baixar o modelo serializado {crop_id}_ndvi.pkl do Hugging Face Hub.
    Em caso de falha de conexão, pacote ausente ou repositório inacessível,
    realiza fallback silencioso e elegante para o arquivo local existente em disco.
    Caso o modelo não exista nem na nuvem nem localmente, levanta FileNotFoundError.
    """
    clean_crop = crop_id.lower().strip()
    filename = f"{clean_crop}_ndvi.pkl"
    local_path = Path(local_dir) / filename
    legacy_path = Path(local_dir) / "ndvi_model.pkl"

    if HF_HUB_AVAILABLE and hf_hub_download is not None:
        try:
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=local_dir,
            )
            logger.info(
                f"📥 Modelo [{clean_crop}] obtido com sucesso do Hugging Face Hub ({repo_id}).",
                extra={"extra_data": {"crop_id": clean_crop, "repo_id": repo_id, "path": str(downloaded_path)}},
            )
            return str(downloaded_path)
        except Exception as exc:
            logger.warning(
                f"⚠️ Falha ao baixar [{filename}] do Hugging Face Hub ({exc}). Ativando fallback local.",
                extra={"extra_data": {"crop_id": clean_crop, "repo_id": repo_id, "error": str(exc)}},
            )

    # Fallback local seguro
    if local_path.exists():
        return str(local_path)
    if clean_crop == "sugarcane" and legacy_path.exists():
        return str(legacy_path)

    raise FileNotFoundError(
        f"Modelo para '{clean_crop}' ({filename}) não foi encontrado no Hugging Face Hub ({repo_id}) "
        f"nem localmente no diretório '{local_dir}'."
    )


def publish_models_to_registry(
    repo_id: str = DEFAULT_HF_REPO_ID,
    token: Optional[str] = None,
    models_dir: str = "src/models",
) -> List[str]:
    """
    Cria (se necessário) o repositório de modelos no Hugging Face Hub e faz o upload
    de todos os artefatos *_ndvi.pkl presentes em models_dir juntamente com o MODEL_CARD.md.
    Retorna a lista dos arquivos enviados.
    """
    auth_token = token or os.getenv("HF_TOKEN")
    api = HfApi(token=auth_token)

    # Cria o repositório no Hub se ainda não existir
    api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)

    uploaded: List[str] = []
    models_path = Path(models_dir)

    # Upload dos arquivos .pkl existentes
    for model_file in sorted(models_path.glob("*_ndvi.pkl")):
        api.upload_file(
            path_or_fileobj=str(model_file),
            path_in_repo=model_file.name,
            repo_id=repo_id,
            repo_type="model",
        )
        uploaded.append(model_file.name)
        logger.info(f"🚀 Modelo [{model_file.name}] publicado no Hugging Face Hub.")

    # Geração e upload do MODEL_CARD oficial como README.md
    model_card_content = generate_model_card()
    card_path = models_path / "MODEL_CARD.md"
    card_path.write_text(model_card_content, encoding="utf-8")

    api.upload_file(
        path_or_fileobj=str(card_path),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model",
    )
    uploaded.append("README.md")
    logger.info("📄 Model Card (README.md) publicado com sucesso no Hugging Face Hub.")

    return uploaded
