from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

class DataClassification(str, Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    regulated = "regulated"
    restricted = "restricted"

class PolicyDecision(str, Enum):
    allow = "allow"
    deny = "deny"
    require_approval = "require_approval"
    redact = "redact"
    escalate = "escalate"

class ToolCall(str, Enum):
    search_documents = "search_documents"
    call_api = "call_api"
    access_records = "access_records"
    write_files = "write_files"
    trigger_workflow = "trigger_workflow"
    send_message = "send_message"

class AIRequestCreate(BaseModel):
    user: str = Field(..., min_length=2)
    role: str
    department: str
    clearance_level: int = Field(..., ge=0, le=5)
    business_purpose: str
    request_type: str
    prompt: str
    data_classification: DataClassification
    tool_calls: List[ToolCall] = []
    approval_status: str = "not_requested"
    device_trust: str = "trusted"
    location_context: str = "corporate"

class IdentityContext(BaseModel):
    user: str
    role: str
    department: str
    clearance_level: int
    business_purpose: str
    device_trust: str
    location_context: str

class PolicyResult(BaseModel):
    decision: PolicyDecision
    reason: str
    risk_tier: str
    redactions_required: bool = False
    human_approval_required: bool = False
    blocked_tool_calls: List[ToolCall] = []

class AIRequestRecord(AIRequestCreate):
    request_id: str
    created_at: datetime
    model: str = "mock-governed-ai"
    prompt_version: str = "lab-v1"
    policy_result: PolicyResult
    final_outcome: str

class DashboardSummary(BaseModel):
    total_requests: int
    denied_requests: int
    high_risk_requests: int
    approval_required: int
    redacted_requests: int
    sensitive_data_attempts: int
    policy_violations: int
    human_approvals: int

class Health(BaseModel):
    status: str
    service: str
    lab_mode: bool
