"""Pydantic v2 schemas for file metadata and paginated listing responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserFileRead(BaseModel):
    """Sanitized file metadata returned to clients."""

    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    owner_id: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedFiles(BaseModel):
    """Response envelope for GET /files/ with pagination metadata."""

    total: int
    limit: int
    offset: int
    items: list[UserFileRead]
