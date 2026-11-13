from fastapi import APIRouter, Depends, Query

from backend.audit import (
    get_audit_logs,
    get_audit_logs_by_resource
)

from backend.dependencies import require_roles


# ============================================================
# AUDIT ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit Trail"]
)


# ============================================================
# GET LATEST AUDIT LOGS
# ADMIN + MANAGER
# ============================================================

@router.get("/logs")
def get_audit_log_list(
    limit: int = Query(
        default=100,
        ge=1,
        le=500
    ),
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER"
        )
    )
):

    return {
        "requested_by": current_user,
        "count": len(get_audit_logs(limit)),
        "audit_logs": get_audit_logs(limit)
    }


# ============================================================
# GET RESOURCE AUDIT HISTORY
# ADMIN + MANAGER
# ============================================================

@router.get("/resource/{resource_type}/{resource_id}")
def get_resource_audit_history(
    resource_type: str,
    resource_id: str,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER"
        )
    )
):

    logs = get_audit_logs_by_resource(
        resource_type=resource_type,
        resource_id=resource_id
    )

    return {
        "requested_by": current_user,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "count": len(logs),
        "audit_logs": logs
    }