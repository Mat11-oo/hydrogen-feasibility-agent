from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: str
    file_type: str
    status: str
    error_reason: str | None = None
    chunk_count: int
    created_at: datetime
