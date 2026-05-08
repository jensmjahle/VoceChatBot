from pydantic import BaseModel


class WebhookTarget(BaseModel):
    gid: int | None = None
    uid: int | None = None


class WebhookDetail(BaseModel):
    content: str
    content_type: str


class WebhookPayload(BaseModel):
    created_at: int
    from_uid: int
    mid: int
    target: WebhookTarget
    detail: WebhookDetail
