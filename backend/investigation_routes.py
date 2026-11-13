from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import require_roles
from backend.investigation import get_alert_investigation


router = APIRouter(
    prefix="/api/v1/investigations",
    tags=["Investigations"]
)


# ============================================================
# ALERT INVESTIGATION
# ============================================================

@router.get("/alerts/{alert_id}")
def alert_investigation(
    alert_id: str,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    try:

        result = get_alert_investigation(
            alert_id
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Alert investigation not found"
            )

        return result

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Investigation error: {str(e)}"
        )