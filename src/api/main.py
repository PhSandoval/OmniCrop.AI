import time
import uuid
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import (
    audit_router,
    farms_router,
    health_router,
    jobs_router,
    mlops_router,
    predict_router,
    reports_router,
    telemetry_router,
)
from src.core.logger import clear_trace_context, logger, set_trace_context

app = FastAPI(
    title="OmniCrop AI — Headless REST API",
    version="1.0.0",
    description=(
        "API RESTful de alta performance do OmniCrop AI. "
        "Disponibiliza serviços desacoplados para inferência de vigor vegetativo (NDVI), "
        "explicabilidade biofísica (XAI Waterfall), cadastro e demarcação geoespacial de propriedades (PostGIS), "
        "ingestão contínua de telemetria IoT de campo (Camada Bronze Azure), trilha de auditoria LGPD "
        "e auditoria estatística de Data Drift (MLOps)."
    ),
    openapi_tags=[
        {
            "name": "Health",
            "description": "Endpoints de prontidão, integridade do serviço e status de Circuit Breakers.",
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
            "description": "Geração sob demanda de laudos e relatórios executivos em PDF com rastreabilidade.",
        },
        {
            "name": "MLOps",
            "description": "Monitoramento estatístico de deriva de dados (PSI e Kolmogorov-Smirnov).",
        },
        {
            "name": "Audit",
            "description": "Trilha imutável de auditoria e conformidade LGPD.",
        },
        {
            "name": "Background Jobs & Cache",
            "description": "Fila assíncrona de processamento em lote (balanço hídrico, laudos) e gerenciamento de cache centralizado.",
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


@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    """Middleware corporativo que gera trace_id, calcula latência e emite logs estruturados em JSON."""
    trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
    user_id = request.headers.get("X-User-ID")
    set_trace_context(trace_id=trace_id, user_id=user_id)

    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Trace-ID"] = trace_id

        logger.info(
            f"HTTP {request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)",
            extra={
                "trace_id": trace_id,
                "latency_ms": duration_ms,
                "extra_data": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "client_ip": request.client.host if request.client else None,
                },
            },
        )
        return response
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(
            f"HTTP {request.method} {request.url.path} falhou após {duration_ms:.2f}ms: {exc}",
            extra={"trace_id": trace_id, "latency_ms": duration_ms},
            exc_info=True,
        )
        raise
    finally:
        clear_trace_context()


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
app.include_router(audit_router, prefix="/api/v1", tags=["Audit"])
app.include_router(jobs_router, prefix="/api/v1", tags=["Background Jobs & Cache"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
