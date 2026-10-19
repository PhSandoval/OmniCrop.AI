"""
Roteador para Background Jobs e Gerenciamento de Cache - OmniCrop AI.
Endpoints assíncronos para cálculo em lote, laudos e monitoramento de cache Redis/memória.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies import AuthContext, get_auth_context
from src.api.schemas.jobs import (
    BatchKpisRequest,
    BatchReportsRequest,
    BatchRetrainRequest,
    CacheClearResponse,
    CacheStatsResponse,
    JobListResponse,
    JobStatusResponse,
    JobSubmissionResponse,
)
from src.core.cache import cache_manager
from src.core.jobs import (
    JobStatus,
    job_manager,
    task_batch_kpis,
    task_batch_reports,
    task_batch_retrain,
)
from src.data.db import log_audit_event

router = APIRouter()


@router.post(
    "/jobs/batch-kpis",
    response_model=JobSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submeter cálculo de balanço hídrico em lote",
    description="Enfileira o processamento assíncrono de balanço hídrico, evapotranspiração e estresse para múltiplos talhões.",
)
def submit_batch_kpis_job(
    request: BatchKpisRequest,
    auth_ctx: AuthContext = Depends(get_auth_context),
) -> JobSubmissionResponse:
    job = job_manager.submit_job(
        job_type="batch_kpis",
        task_fn=task_batch_kpis,
        payload=request.model_dump(),
        farm_ids=request.farm_ids,
        crop_id=request.crop_id,
        lat=request.lat,
        lon=request.lon,
    )
    try:
        log_audit_event(
            user_id=auth_ctx.user_id,
            action="SUBMIT_JOB_BATCH_KPIS",
            entity_type="job",
            entity_id=job.job_id,
            details={"farm_count": len(request.farm_ids), "crop_id": request.crop_id},
            access_token=auth_ctx.access_token,
        )
    except Exception:
        pass

    return JobSubmissionResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        status=job.status.value,
        message=f"Tarefa de balanço hídrico para {len(request.farm_ids)} talhões enfileirada com sucesso.",
        created_at=job.created_at,
    )


@router.post(
    "/jobs/batch-reports",
    response_model=JobSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submeter geração de laudos em lote",
    description="Dispara worker em background para gerar laudos técnicos executivos em lote para os talhões solicitados.",
)
def submit_batch_reports_job(
    request: BatchReportsRequest,
    auth_ctx: AuthContext = Depends(get_auth_context),
) -> JobSubmissionResponse:
    job = job_manager.submit_job(
        job_type="batch_reports",
        task_fn=task_batch_reports,
        payload=request.model_dump(),
        farm_ids=request.farm_ids,
        crop_id=request.crop_id,
    )
    try:
        log_audit_event(
            user_id=auth_ctx.user_id,
            action="SUBMIT_JOB_BATCH_REPORTS",
            entity_type="job",
            entity_id=job.job_id,
            details={"farm_count": len(request.farm_ids), "crop_id": request.crop_id},
            access_token=auth_ctx.access_token,
        )
    except Exception:
        pass

    return JobSubmissionResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        status=job.status.value,
        message=f"Geração em lote de {len(request.farm_ids)} laudos enfileirada com sucesso.",
        created_at=job.created_at,
    )


@router.post(
    "/jobs/batch-retrain",
    response_model=JobSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submeter calibração de modelos em background",
    description="Dispara rotina assíncrona de auditoria e calibração de modelos para as culturas especificadas.",
)
def submit_batch_retrain_job(
    request: BatchRetrainRequest,
    auth_ctx: AuthContext = Depends(get_auth_context),
) -> JobSubmissionResponse:
    job = job_manager.submit_job(
        job_type="model_retrain",
        task_fn=task_batch_retrain,
        payload=request.model_dump(),
        crops=request.crops,
    )
    try:
        log_audit_event(
            user_id=auth_ctx.user_id,
            action="SUBMIT_JOB_BATCH_RETRAIN",
            entity_type="job",
            entity_id=job.job_id,
            details={"crops": request.crops},
            access_token=auth_ctx.access_token,
        )
    except Exception:
        pass

    return JobSubmissionResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        status=job.status.value,
        message=f"Auditoria e calibração de {len(request.crops)} culturas enfileirada com sucesso.",
        created_at=job.created_at,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Consultar status de background job",
    description="Recupera o progresso percentual, status e payload de resultados de um job em processamento ou finalizado.",
)
def get_job_status(job_id: str) -> JobStatusResponse:
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job com identificador '{job_id}' não foi encontrado.",
        )
    return JobStatusResponse(**job.to_dict())


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=JobStatusResponse,
    summary="Cancelar background job",
    description="Interrompe uma tarefa que esteja pendente ou em execução na fila.",
)
def cancel_job(
    job_id: str,
    auth_ctx: AuthContext = Depends(get_auth_context),
) -> JobStatusResponse:
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job com identificador '{job_id}' não foi encontrado.",
        )
    success = job_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não é possível cancelar o job '{job_id}' pois já se encontra no estado '{job.status.value}'.",
        )
    try:
        log_audit_event(
            user_id=auth_ctx.user_id,
            action="CANCEL_JOB",
            entity_type="job",
            entity_id=job_id,
            details={"previous_status": job.status.value},
            access_token=auth_ctx.access_token,
        )
    except Exception:
        pass

    updated_job = job_manager.get_job(job_id)
    return JobStatusResponse(**updated_job.to_dict())  # type: ignore


@router.get(
    "/jobs",
    response_model=JobListResponse,
    summary="Listar background jobs",
    description="Retorna o histórico de tarefas assíncronas registradas com filtro opcional por status.",
)
def list_jobs(
    job_status: Optional[str] = Query(default=None, alias="status", description="Filtrar por status do job"),
    limit: int = Query(default=50, ge=1, le=200, description="Limite máximo de itens"),
) -> JobListResponse:
    jobs = job_manager.list_jobs(limit=limit, status=job_status)
    return JobListResponse(
        jobs=[JobStatusResponse(**j.to_dict()) for j in jobs],
        total=len(jobs),
    )


@router.get(
    "/cache/stats",
    response_model=CacheStatsResponse,
    summary="Estatísticas operacionais do cache",
    description="Retorna telemetria de hits, misses, taxa de acerto e tipo de backend do cache centralizado.",
)
def get_cache_stats() -> CacheStatsResponse:
    stats = cache_manager.get_stats()
    return CacheStatsResponse(**stats)


@router.post(
    "/cache/clear",
    response_model=CacheClearResponse,
    summary="Limpar cache corporativo",
    description="Invalida todas as chaves em cache (Redis ou memória) e zera os contadores operacionais.",
)
def clear_cache(
    auth_ctx: AuthContext = Depends(get_auth_context),
) -> CacheClearResponse:
    cache_manager.clear()
    try:
        log_audit_event(
            user_id=auth_ctx.user_id,
            action="CLEAR_CACHE",
            entity_type="cache",
            entity_id="central_cache",
            details={"status": "cleared"},
            access_token=auth_ctx.access_token,
        )
    except Exception:
        pass

    return CacheClearResponse(
        status="ok",
        message="Cache centralizado limpo com sucesso.",
    )
