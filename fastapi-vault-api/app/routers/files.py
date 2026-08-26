"""
File management routes.

POST   /files/upload            - upload a new file (image/PDF, size-limited)
GET    /files/                  - list the current user's files (paginated + filterable)
GET    /files/{file_id}/download - stream a file back to its owner
DELETE /files/{file_id}         - delete a file (metadata + on-disk object)

Every route enforces that a user may only see/download/delete their OWN
files — cross-user access always returns 404 (never 403), so the existence
of another user's file is not leaked.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.user_file import UserFile
from app.schemas.file import PaginatedFiles, UserFileRead
from app.utils.file_helpers import build_storage_path, generate_stored_filename, save_upload_stream

router = APIRouter(prefix="/files", tags=["Files"])


@router.post(
    "/upload",
    response_model=UserFileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
    description=(
        "Accepts image (JPEG/PNG/GIF) or PDF uploads. Files are streamed to "
        "disk under a UUID-derived filename to prevent collisions and to "
        "avoid exposing the original filename in the storage path. Uploads "
        "exceeding the configured size limit are rejected with 413."
    ),
)
async def upload_file(
    upload: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserFile:
    stored_filename = generate_stored_filename(upload.content_type)
    destination_path = build_storage_path(stored_filename)

    size_bytes = await save_upload_stream(upload, destination_path)

    db_file = UserFile(
        original_filename=upload.filename or stored_filename,
        stored_filename=stored_filename,
        content_type=upload.content_type,
        size_bytes=size_bytes,
        owner_id=current_user.id,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


@router.get(
    "/",
    response_model=PaginatedFiles,
    summary="List the current user's files",
    description=(
        "Returns a paginated list of the authenticated user's uploaded "
        "files. Supports `limit`/`offset` pagination and optional filtering "
        "by content type or filename substring."
    ),
)
def list_files(
    limit: int = Query(default=20, ge=1, le=100, description="Max number of items to return"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    content_type: str | None = Query(default=None, description="Exact content-type filter, e.g. 'application/pdf'"),
    filename_contains: str | None = Query(default=None, description="Case-insensitive substring match on original filename"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedFiles:
    stmt = select(UserFile).where(UserFile.owner_id == current_user.id)

    if content_type:
        stmt = stmt.where(UserFile.content_type == content_type)
    if filename_contains:
        stmt = stmt.where(UserFile.original_filename.ilike(f"%{filename_contains}%"))

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    items = db.execute(
        stmt.order_by(UserFile.uploaded_at.desc()).limit(limit).offset(offset)
    ).scalars().all()

    return PaginatedFiles(total=total or 0, limit=limit, offset=offset, items=list(items))


def _get_owned_file_or_404(file_id: str, db: Session, current_user: User) -> UserFile:
    """Fetch a file by id, scoped to the current user. 404s if absent or not owned."""
    db_file = db.get(UserFile, file_id)
    if db_file is None or db_file.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return db_file


@router.get(
    "/{file_id}/download",
    summary="Download a file",
    description="Streams the file back to its owner. Returns 404 for files that don't exist or belong to another user.",
)
def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    db_file = _get_owned_file_or_404(file_id, db, current_user)
    storage_path = build_storage_path(db_file.stored_filename)

    if not os.path.exists(storage_path):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="File metadata exists but the underlying object is missing",
        )

    return FileResponse(
        path=storage_path,
        media_type=db_file.content_type,
        filename=db_file.original_filename,
    )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a file",
    description="Deletes a file's metadata and its on-disk object. Returns 404 for files that don't exist or belong to another user.",
)
def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    db_file = _get_owned_file_or_404(file_id, db, current_user)
    storage_path = build_storage_path(db_file.stored_filename)

    if os.path.exists(storage_path):
        os.remove(storage_path)

    db.delete(db_file)
    db.commit()
