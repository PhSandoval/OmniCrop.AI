"""
Ponto de entrada principal da API RESTful Headless do OmniCrop AI.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import (
    farms_router,
    health_router,
    mlops_router,
    predict_router,
    reports_router,
    telemetry_router,
)

app = FastAPI(
    title="OmniCrop AI — Headless REST API",
    version="1.0.0",
    description=(
        "API RESTful de alta performance do OmniCrop AI. "
        "Disponibiliza serviços desacoplados para inferência de vigor vegetativo (NDVI), "
        "explicabilidade biofísica (XAI Waterfall), cadastro e demarcação geoespacial de propriedades (PostGIS), "
        "ingestão contínua de telemetria IoT de campo (Camada Bronze Azure) e auditoria estatística de Data Drift (MLOps)."
    ),
    openapi_tags=[
        {
            "name": "Health",
            "description": "Endpoints de prontidão e integridade do serviço.",
        },
        {
            "name": "Predict & XAI",
            "description": "Satélite virtual para estimativa de NDVI, explicabilidade marginal e recomendações DSS.",
        },
        {
            "name": "Farms & Geo",
            "description": "Operações CRUD de propriedades agrícolas com suporte a polígonos GeoJSON e multi-tenancy RLS.",
        },
        {
            "name": "IoT Telemetry",
            "description": "Ingestão de leituras de solo, temperatura e molhamento foliar na Camada Bronze.",
        },
        {
            "name": "Reports",
            "description": "Geração sob demanda de laudos e relatórios executivos em PDF.",
        },
        {
            "name": "MLOps",
            "description": "Monitoramento estatístico de deriva de dados (PSI e Kolmogorov-Smirnov).",
        },
    ],
)

# Configuração de CORS para permitir acesso por clientes Web, Mobile e ERPs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotImplementedError)
def handle_not_implemented_error(request: Request, exc: NotImplementedError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_code": "CROP_IN_CALIBRATION"},
    )


# Registro de Roteadores Modulares
app.include_router(health_router, tags=["Health"])
app.include_router(predict_router, prefix="/api/v1", tags=["Predict & XAI"])
app.include_router(farms_router, prefix="/api/v1", tags=["Farms & Geo"])
app.include_router(telemetry_router, prefix="/api/v1", tags=["IoT Telemetry"])
app.include_router(reports_router, prefix="/api/v1", tags=["Reports"])
app.include_router(mlops_router, prefix="/api/v1", tags=["MLOps"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
