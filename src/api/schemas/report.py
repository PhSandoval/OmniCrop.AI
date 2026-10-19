"""
Schemas Pydantic v2 para Emissão de Relatórios Executivos em PDF.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    """Parâmetros para renderização do relatório executivo agronômico."""
    farm_name: str = Field(..., min_length=1, description="Nome da propriedade ou talhão")
    city: str = Field(..., min_length=1, description="Município e UF")
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Telemetria climática (Open-Meteo) com chuva acumulada e GDA",
    )
    resultado: Dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnóstico preditivo de NDVI e parecer do DSS",
    )
    gold_kpis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Indicadores consolidados da Camada Ouro (Balanço Hídrico, Veranico)",
    )
    xai_res: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Decomposição marginal do XAI Waterfall",
    )
    as_base64: bool = Field(
        default=False,
        description="Se verdadeiro, retorna o PDF codificado em Base64 no corpo JSON",
    )


class ReportGenerateResponse(BaseModel):
    """Metadados e conteúdo do relatório executivo quando solicitado em formato JSON."""
    filename: str = Field(..., description="Nome do arquivo PDF gerado")
    content_type: str = Field(default="application/pdf", description="Tipo MIME do documento")
    pdf_base64: Optional[str] = Field(default=None, description="Arquivo PDF em base64")
    size_bytes: int = Field(..., description="Tamanho em bytes do arquivo PDF")
