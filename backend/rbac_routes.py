from fastapi import APIRouter, Depends

from backend.dependencies import (
    get_current_user,
    require_roles
)


# ============================================================
# RBAC ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/rbac",
    tags=["RBAC"]
)


# ============================================================
# ANY AUTHENTICATED USER
# ============================================================

@router.get("/profile")
def authenticated_profile(
    current_user=Depends(get_current_user)
):

    return {
        "message": "Authenticated user access granted",
        "user": current_user
    }


# ============================================================
# ADMIN ONLY
# ============================================================

@router.get("/admin-only")
def admin_only(
    current_user=Depends(
        require_roles("ADMIN")
    )
):

    return {
        "message": "Admin access granted",
        "user": current_user
    }


# ============================================================
# ADMIN + MANAGER
# ============================================================

@router.get("/management")
def management_access(
    current_user=Depends(
        require_roles("ADMIN", "MANAGER")
    )
):

    return {
        "message": "Management access granted",
        "user": current_user
    }


# ============================================================
# ADMIN + MANAGER + ANALYST
# ============================================================

@router.get("/investigation")
def investigation_access(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST"
        )
    )
):

    return {
        "message": "Investigation access granted",
        "user": current_user
    }


# ============================================================
# ALL AUTHENTICATED ROLES
# ============================================================

@router.get("/read-only")
def read_only_access(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    return {
        "message": "Read-only access granted",
        "user": current_user
    }