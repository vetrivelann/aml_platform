from pydantic import BaseModel, Field


# ============================================================
# NOTIFICATION MODELS
# ============================================================

class NotificationCreate(BaseModel):

    notification_type: str = Field(
        min_length=2,
        max_length=50
    )

    recipient: str = Field(
        min_length=2,
        max_length=100
    )

    subject: str = Field(
        min_length=2,
        max_length=200
    )

    message: str = Field(
        min_length=2
    )

    priority: str = "MEDIUM"


class NotificationResponse(BaseModel):

    notification_id: str

    notification_type: str

    recipient: str

    subject: str

    message: str

    priority: str

    status: str

    created_at: str