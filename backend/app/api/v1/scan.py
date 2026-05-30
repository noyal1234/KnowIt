import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_providers.base import AuthUser
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.schemas import ScanRequest, ScanResponse
from app.pipeline.orchestrator import run_scan_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    body: ScanRequest,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    try:
        return await run_scan_pipeline(
            session,
            current_user.id,
            barcode=body.barcode,
            ingredient_text=body.ingredient_text,
            image_base64=body.image_base64,
            storage_path=body.storage_path,
            product_hint=body.product_hint,
            region=body.region,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(
            "event=ScanPipelineFailed user_id=%s error=%s",
            current_user.id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Scan pipeline failed. Please try again.",
        ) from exc
