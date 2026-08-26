"""UserFile ORM model — represents an uploaded file owned by a User."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserFile(Base):
    __tablename__ = "user_files"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Original filename as uploaded by the client (for display purposes only).
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # UUID-based filename actually used on disk, preventing collisions and
    # preventing path traversal / guessing of other users' files.
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner: Mapped["User"] = relationship("User", back_populates="files")

    def __repr__(self) -> str:
        return f"<UserFile id={self.id} owner_id={self.owner_id} name={self.original_filename}>"
