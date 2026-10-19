"""
Endpoints para Emissão e Download de Relatórios Executivos em PDF.
"""
import base64
import re
from fastapi import APIRouter, HTTPException, Response, status

from src.api.schemas.report import (
    ReportGenerateRequest,
    ReportGenerateResponse,
)
from src.reports.pdf import generate_pdf_report

router = APIRouter()


@router.post(
    "/reports/pdf",
    response_model=ReportGenerateResponse,
    responses={
        200: {
            "content": {"application/pdf": {}, "application/json": {}},
            "description": "Arquivo binário PDF ou JSON com payload base64.",
        }
    },
    status_code=status.HTTP_200_OK,
    summary="Gerar Laudo Executivo em PDF com KPIs Ouro e XAI",
    description=(
        "Emite o relatório agronômico oficial em formato PDF contendo indicadores da Camada Ouro, "
        "diagnóstico de vigor vegetativo, parecer do DSS e explicabilidade de inteligência artificial. "
        "Pode retornar o arquivo binário direto (stream) ou serializado em base64 via JSON."
    ),
)
def generate_pdf_report_endpoint(req: ReportGenerateRequest):
    try:
        pdf_bytes = generate_pdf_report(
            farm_name=req.farm_name,
            city=req.city,
            payload=req.payload,
            resultado=req.resultado,
            gold_kpis=req.gold_kpis,
            xai_res=req.xai_res,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao gerar relatório executivo em PDF: {e}",
        )

    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", req.farm_name).lower()
    filename = f"relatorio_executivo_{clean_name}.pdf"

    if req.as_base64:
        encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        return ReportGenerateResponse(
            filename=filename,
            content_type="application/pdf",
            pdf_base64=encoded_pdf,
            size_bytes=len(pdf_bytes),
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
