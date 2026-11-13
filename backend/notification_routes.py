from fastapi import APIRouter, HTTPException

from backend.notification_models import (
    NotificationCreate
)

from backend.notifications import (
    create_notification,
    get_notifications,
    get_notification_by_id,
    update_notification_status
)


# ============================================================
# NOTIFICATION ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"]
)


# ============================================================
# CREATE NOTIFICATION
# ============================================================

@router.post("/")
def create_notification_route(
    notification: NotificationCreate
):

    try:

        result = create_notification(

            notification_type=
                notification.notification_type,

            recipient=
                notification.recipient,

            subject=
                notification.subject,

            message=
                notification.message,

            priority=
                notification.priority
        )

        return {
            "message":
                "Notification created successfully",

            "notification":
                result
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ============================================================
# GET ALL NOTIFICATIONS
# ============================================================

@router.get("/")
def get_all_notifications():

    try:

        notifications = get_notifications()

        return {

            "count":
                len(notifications),

            "notifications":
                notifications
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ============================================================
# GET NOTIFICATION BY ID
# ============================================================

@router.get("/{notification_id}")
def get_notification(
    notification_id: str
):

    try:

        notification = (
            get_notification_by_id(
                notification_id
            )
        )

        if not notification:

            raise HTTPException(
                status_code=404,
                detail="Notification not found"
            )

        return {
            "notification":
                notification
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ============================================================
# UPDATE NOTIFICATION STATUS
# ============================================================

@router.patch("/{notification_id}/status")
def update_status(
    notification_id: str,
    status: str
):

    try:

        result = update_notification_status(
            notification_id,
            status
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Notification not found"
            )

        return {

            "message":
                "Notification status updated successfully",

            "notification":
                result
        }

    except HTTPException:

        raise

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )