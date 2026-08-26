"""
File-handling helpers: UUID-based storage naming, extension validation, and
async streaming save-to-disk with a size cap enforced while streaming (so an
oversized upload is rejected without buffering the whole file in memory).
"""

import os
import uuid

from fastapi import HTTPException, UploadFile, status

from app.config import settings

# Map allowed MIME types to a safe extension used for the stored file.
_EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "application/pdf": ".pdf",
}


def validate_content_type(content_type: str | None) -> str:
    """Ensure the uploaded file's content type is allowed. Returns the extension to use."""
    if content_type not in settings.allowed_content_types_list:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported content type '{content_type}'. "
                f"Allowed types: {', '.join(settings.allowed_content_types_list)}"
            ),
        )
    return _EXTENSION_BY_CONTENT_TYPE.get(content_type, "")


def generate_stored_filename(content_type: str) -> str:
    """Generate a collision-proof UUID-based filename for disk storage."""
    extension = validate_content_type(content_type)
    return f"{uuid.uuid4().hex}{extension}"


async def save_upload_stream(upload_file: UploadFile, destination_path: str) -> int:
    """
    Stream an UploadFile to disk in chunks, enforcing MAX_UPLOAD_SIZE_MB.

    Returns the total number of bytes written. Raises HTTP 413 and removes
    any partially-written file if the size limit is exceeded.
    """
    chunk_size = 1024 * 1024  # 1 MB
    total_bytes = 0

    try:
        with open(destination_path, "wb") as out_file:
            while chunk := await upload_file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_size_bytes:
                    out_file.close()
                    os.remove(destination_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB",
                    )
                out_file.write(chunk)
    finally:
        await upload_file.close()

    return total_bytes


def build_storage_path(stored_filename: str) -> str:
    """Return the absolute path where a stored file lives on disk."""
    return os.path.join(settings.UPLOAD_DIR, stored_filename)
