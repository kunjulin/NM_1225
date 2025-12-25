from __future__ import annotations

from pydantic import BaseModel


class OutboxRow(BaseModel):
    id: str
    caseId: str
    operation: str
    status: str
    retryCount: int
    lastError: str | None
    createdAt: str
    updatedAt: str
    nextRetryAt: str | None
