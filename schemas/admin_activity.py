from pydantic import BaseModel


class AdminActivityOut(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: str
    admin_name: str | None = None
    payload_json: str | None = None
    created_at: str
