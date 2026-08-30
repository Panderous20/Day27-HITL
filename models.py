from pydantic import BaseModel


class AuditEntry(BaseModel):
    timestamp: str
    agent_id: str
    action: str
    confidence: float
    reviewer_id: str
    decision: str
