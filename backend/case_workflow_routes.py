from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import require_roles
from backend.case_workflow import (
    create_case_from_alert,
    assign_case,
    update_case_disposition,
    close_case
)


router = APIRouter(
    prefix="/api/v1/case-workflow",
    tags=["Case Workflow"]
)


# ============================================================
# CREATE CASE FROM ALERT
# ============================================================

@router.post("/alerts/{alert_id}/create")
def create_case(
    alert_id: str,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST"
        )
    )
):

    try:

        result = create_case_from_alert(
            alert_id=alert_id,
            user_id=current_user["user_id"],
            username=current_user["username"],
            user_role=current_user["role"]
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Alert not found"
            )

        return result

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Case creation failed: {str(e)}"
        )


# ============================================================
# ASSIGN CASE
# ============================================================

@router.patch("/{case_id}/assign")
def assign_case_to_analyst(
    case_id: str,
    assigned_to: str,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER"
        )
    )
):

    try:

        result = assign_case(
            case_id=case_id,
            assigned_to=assigned_to,
            user_id=current_user["user_id"],
            username=current_user["username"],
            user_role=current_user["role"]
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Case not found"
            )

        return result

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Case assignment failed: {str(e)}"
        )


# ============================================================
# UPDATE DISPOSITION
# ============================================================

@router.patch("/{case_id}/disposition")
def update_disposition(
    case_id: str,
    disposition: str,
    notes: str | None = None,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST"
        )
    )
):

    try:

        result = update_case_disposition(
            case_id=case_id,
            disposition=disposition,
            notes=notes,
            user_id=current_user["user_id"],
            username=current_user["username"],
            user_role=current_user["role"]
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Case not found"
            )

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Disposition update failed: {str(e)}"
        )


# ============================================================
# CLOSE CASE
# ============================================================

@router.patch("/{case_id}/close")
def close_aml_case(
    case_id: str,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST"
        )
    )
):

    try:

        result = close_case(
            case_id=case_id,
            user_id=current_user["user_id"],
            username=current_user["username"],
            user_role=current_user["role"]
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Case not found"
            )

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Case closure failed: {str(e)}"
        )