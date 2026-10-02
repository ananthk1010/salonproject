from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_classify_service
from app.jev.client import JevUpstreamError
from app.jev.replay import ReplayMiss
from app.rate_limit import rate_limit
from app.schemas.classify import ClassifyRequest, ClassifyResponse
from app.services.classify_service import ClassifyService, InteractionNotFound

router = APIRouter(tags=["classify"])


@router.post("/api/classify", response_model=ClassifyResponse, dependencies=[Depends(rate_limit)])
def classify(
    req: ClassifyRequest,
    service: ClassifyService = Depends(get_classify_service),
) -> ClassifyResponse:
    try:
        return service.classify(req)
    except InteractionNotFound as exc:
        raise HTTPException(status_code=404, detail=f"no such interaction: {exc}") from exc
    except ReplayMiss as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except JevUpstreamError as exc:
        raise HTTPException(status_code=502, detail=f"Jev gateway error: {exc}") from exc
