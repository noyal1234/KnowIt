from fastapi import APIRouter, Depends, HTTPException

from app.core.auth_providers.base import AuthUser
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.schemas import ScanRequest, ScanResponse
from app.pipeline.orchestrator import run_scan_pipeline
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("", response_model=ScanResponse)
async def create_scan(
    body: ScanRequest,
    current_user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    if not body.barcode and not body.ingredient_text and not body.image_base64 and not body.storage_path:
        raise HTTPException(
            status_code=400,
            detail="Provide barcode, ingredient_text, image_base64, or storage_path",
        )
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
        raise HTTPException(status_code=500, detail=f"Scan pipeline failed: {exc}") from exc
