"""
Schemas Pydantic v2 para o Assistente de Manejo Agronômico (Copilot) - OmniCrop AI.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class CopilotAskRequest(BaseModel):
    """Payload de consulta ao Assistente de Manejo Agronômico."""
    question: str = Field(..., min_length=2, description="Pergunta ou instrução técnica do agrônomo/gestor")
    farm_id: Optional[str] = Field(default=None, description="Identificador da fazenda no Supabase")
    farm_name: str = Field(default="Fazenda Modelo", description="Nome da propriedade ou talhão")
    crop_id: str = Field(default="sugarcane", description="Identificador canônico da cultura agrícola")
    city: Optional[str] = Field(default="Ribeirão Preto, SP", description="Município da lavoura")
    lat: float = Field(default=-21.17, description="Latitude da área monitorada")
    lon: float = Field(default=-47.81, description="Longitude da área monitorada")
    ndvi_base: float = Field(default=0.65, description="NDVI base observado")
    ndvi_proj: float = Field(default=0.68, description="NDVI projetado pelo modelo")
    cenario_nome: str = Field(default="Manejo Padrão", description="Cenário de simulação ativo")
    gold_kpis: Optional[Dict[str, Any]] = Field(default=None, description="Indicadores consolidados da Camada Ouro")
    xai_res: Optional[Dict[str, Any]] = Field(default=None, description="Decomposição marginal e explicabilidade XAI")
    dss: Optional[Dict[str, Any]] = Field(default=None, description="Decisão agronômica do motor especialista DSS")


class CopilotAskResponse(BaseModel):
    """Resposta técnica estruturada emitida pelo Copilot."""
    question: str = Field(..., description="Pergunta original enviada")
    answer: str = Field(..., description="Parecer técnico fundamentado com plano de ação")
    source: str = Field(..., description="Origem da resposta ('gemini' ou 'deterministic_fallback')")
    model: str = Field(..., description="Identificador do modelo ou motor de inferência")
    crop_id: str = Field(..., description="Cultura avaliada")
    farm_name: str = Field(..., description="Fazenda contextualizada")
    created_at: str = Field(..., description="Timestamp ISO da resposta")
