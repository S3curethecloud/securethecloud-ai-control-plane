from datetime import datetime, timezone
from enum import Enum
from typing import List, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class DataClassification(str, Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    regulated = "regulated"
    restricted = "restricted"


class ToolCall(str, Enum):
    search_documents = "search_documents"
    call_api = "call_api"
    access_records = "access_records"
    write_files = "write_files"
    trigger_workflow = "trigger_workflow"
    send_message = "send_message"


class PolicyDecision(str, Enum):
    allow = "allow"
    deny = "deny"
    require_approval = "require_approval"
    redact = "redact"
    escalate = "escalate"


class AIRequestCreate(BaseModel):
    user: str = Field(min_length=2)
    role: str
    department: str
    clearance_level: int = Field(ge=0, le=5)
    business_purpose: str
    request_type: str
    prompt: str
    data_classification: DataClassification
    tool_calls: List[ToolCall] = []
    approval_status: str = "not_requested"
    device_trust: str = "trusted"
    location_context: str = "corporate"


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
    approval_status: str = "not_requested"
    reviewer: str | None = None
    reviewer_action: str | None = None
    reviewer_note: str | None = None
    reviewed_at: datetime | None = None


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


class ApprovalAction(BaseModel):
    action: Literal["approve", "reject", "escalate"]
    reviewer: str = "Security Officer"
    note: str = "Reviewed in Phase 8 Human Approval Workspace"


class ToolFirewallDecision(BaseModel):
    tool: ToolCall
    status: Literal["allowed", "blocked", "requires_approval", "redacted"]
    reason: str


app = FastAPI(
    title="SecureTheCloud AI Control Plane API",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


REQUESTS: list[AIRequestRecord] = []


def now() -> datetime:
    return datetime.now(timezone.utc)


def evaluate_tool_firewall(request: AIRequestCreate) -> list[ToolFirewallDecision]:
    decisions: list[ToolFirewallDecision] = []

    for tool in request.tool_calls:
        status: Literal["allowed", "blocked", "requires_approval", "redacted"] = "allowed"
        reason = "Tool call is within current policy boundary."

        sensitive = request.data_classification in {
            DataClassification.confidential,
            DataClassification.regulated,
            DataClassification.restricted,
        }

        if request.approval_status == "rejected":
            status = "blocked"
            reason = "Human reviewer rejected the workflow; tool execution is blocked."

        elif request.approval_status == "escalated":
            status = "blocked"
            reason = "Request is escalated; tool execution is blocked until additional governance review."

        elif request.data_classification == DataClassification.confidential:
            if tool == ToolCall.search_documents:
                status = "redacted"
                reason = "Confidential data may be searched only with redaction and evidence capture."
            elif tool in {ToolCall.access_records, ToolCall.write_files}:
                status = "blocked"
                reason = f"{tool.value} is blocked for confidential data without stronger approval evidence."
            elif tool in {ToolCall.call_api, ToolCall.trigger_workflow, ToolCall.send_message}:
                status = "requires_approval"
                reason = f"{tool.value} requires human approval for confidential workflow execution."

        elif request.data_classification in {DataClassification.regulated, DataClassification.restricted}:
            if request.approval_status == "approved":
                status = "allowed"
                reason = f"{tool.value} is allowed because human approval evidence is present."
            else:
                status = "requires_approval"
                if tool == ToolCall.search_documents:
                    reason = "Restricted or regulated document search requires approval before retrieval."
                elif tool == ToolCall.call_api:
                    reason = "API access requires approval before regulated data can leave the control plane."
                elif tool == ToolCall.access_records:
                    reason = "Restricted data requires approval before access_records can execute."
                elif tool == ToolCall.write_files:
                    reason = "write_files is blocked until approval because AI must not alter governed records without review."
                elif tool == ToolCall.trigger_workflow:
                    reason = "trigger_workflow requires approval because it may execute downstream business action."
                elif tool == ToolCall.send_message:
                    reason = "send_message is blocked until approval because AI cannot send messages without human review."

        decisions.append(
            ToolFirewallDecision(
                tool=tool,
                status=status,
                reason=reason,
            )
        )

    return decisions


def blocked_tools_for(request: AIRequestCreate) -> list[ToolCall]:
    return [
        decision.tool
        for decision in evaluate_tool_firewall(request)
        if decision.status in {"blocked", "requires_approval"}
    ]


def evaluate_policy(request: AIRequestCreate) -> PolicyResult:
    blocked = blocked_tools_for(request)

    if request.approval_status == "rejected":
        return PolicyResult(
            decision=PolicyDecision.deny,
            reason="Human reviewer rejected the AI workflow request.",
            risk_tier="critical",
            blocked_tool_calls=request.tool_calls,
        )

    if request.approval_status == "escalated":
        return PolicyResult(
            decision=PolicyDecision.escalate,
            reason="Human reviewer escalated the request for additional governance review.",
            risk_tier="critical",
            human_approval_required=True,
            blocked_tool_calls=blocked,
        )

    if request.data_classification == DataClassification.restricted:
        if request.clearance_level < 4:
            return PolicyResult(
                decision=PolicyDecision.deny,
                reason="Clearance level is too low for regulated or restricted data.",
                risk_tier="critical",
                blocked_tool_calls=blocked,
            )

        if request.approval_status != "approved":
            return PolicyResult(
                decision=PolicyDecision.require_approval,
                reason="Restricted data requires human approval before AI access or tool execution.",
                risk_tier="high",
                human_approval_required=True,
                blocked_tool_calls=blocked,
            )

        return PolicyResult(
            decision=PolicyDecision.allow,
            reason="Restricted request has sufficient identity context and human approval evidence.",
            risk_tier="high",
        )

    if request.data_classification == DataClassification.regulated:
        if request.clearance_level < 3:
            return PolicyResult(
                decision=PolicyDecision.deny,
                reason="Clearance level is too low for regulated data.",
                risk_tier="critical",
                blocked_tool_calls=blocked,
            )

        if request.approval_status != "approved":
            return PolicyResult(
                decision=PolicyDecision.require_approval,
                reason="Regulated data requires human approval before governed AI processing.",
                risk_tier="high",
                human_approval_required=True,
                blocked_tool_calls=blocked,
            )

        return PolicyResult(
            decision=PolicyDecision.allow,
            reason="Regulated request has approval evidence and sufficient identity context.",
            risk_tier="high",
        )

    if request.data_classification == DataClassification.confidential:
        return PolicyResult(
            decision=PolicyDecision.redact,
            reason="Confidential data may be summarized only with redaction and evidence capture.",
            risk_tier="medium",
            redactions_required=True,
            blocked_tool_calls=blocked,
        )

    return PolicyResult(
        decision=PolicyDecision.allow,
        reason="Request is within approved low-sensitivity AI assistance boundaries.",
        risk_tier="low",
    )


def create_record(request: AIRequestCreate) -> AIRequestRecord:
    result = evaluate_policy(request)
    return AIRequestRecord(
        **request.model_dump(),
        request_id=f"req_{uuid4().hex[:10]}",
        created_at=now(),
        policy_result=result,
        final_outcome=result.decision.value,
    )


def seed() -> None:
    if REQUESTS:
        return

    examples = [
        AIRequestCreate(
            user="Jordan Lee",
            role="Engineer",
            department="IT",
            clearance_level=3,
            business_purpose="Incident investigation",
            request_type="Analyze security logs",
            prompt="Summarize confidential security logs.",
            data_classification=DataClassification.confidential,
            tool_calls=[ToolCall.search_documents],
        ),
        AIRequestCreate(
            user="Mina Patel",
            role="Care Coordinator",
            department="Healthcare",
            clearance_level=2,
            business_purpose="Care review",
            request_type="Review healthcare notes",
            prompt="Summarize regulated patient notes.",
            data_classification=DataClassification.regulated,
            tool_calls=[ToolCall.access_records],
        ),
        AIRequestCreate(
            user="Avery Chen",
            role="Risk Analyst",
            department="Finance",
            clearance_level=5,
            business_purpose="Board risk packet",
            request_type="Generate executive risk report",
            prompt="Generate executive summary from restricted financial records.",
            data_classification=DataClassification.restricted,
            tool_calls=[ToolCall.search_documents],
            approval_status="approved",
        ),
        AIRequestCreate(
            user="Taylor Morgan",
            role="Analyst",
            department="Finance",
            clearance_level=4,
            business_purpose="Quarterly risk review",
            request_type="Summarize sensitive records",
            prompt="Summarize restricted financial customer records for executive review.",
            data_classification=DataClassification.restricted,
            tool_calls=[ToolCall.search_documents, ToolCall.access_records],
            approval_status="not_requested",
        ),
    ]

    for item in examples:
        REQUESTS.append(create_record(item))


@app.on_event("startup")
def startup() -> None:
    seed()


@app.post("/api/tool-firewall/preview", response_model=list[ToolFirewallDecision])
def tool_firewall_preview(request: AIRequestCreate):
    return evaluate_tool_firewall(request)


@app.get("/health", response_model=Health)
def health():
    return Health(
        status="ok",
        service="securethecloud-ai-control-plane",
        lab_mode=True,
    )


@app.get("/api/dashboard", response_model=DashboardSummary)
def dashboard():
    return DashboardSummary(
        total_requests=len(REQUESTS),
        denied_requests=sum(r.policy_result.decision == PolicyDecision.deny for r in REQUESTS),
        high_risk_requests=sum(r.policy_result.risk_tier in {"high", "critical"} for r in REQUESTS),
        approval_required=sum(r.policy_result.decision == PolicyDecision.require_approval for r in REQUESTS),
        redacted_requests=sum(r.policy_result.decision == PolicyDecision.redact for r in REQUESTS),
        sensitive_data_attempts=sum(
            r.data_classification in {DataClassification.confidential, DataClassification.regulated, DataClassification.restricted}
            for r in REQUESTS
        ),
        policy_violations=sum(r.policy_result.decision in {PolicyDecision.deny, PolicyDecision.escalate} for r in REQUESTS),
        human_approvals=sum(r.approval_status == "approved" for r in REQUESTS),
    )


@app.get("/api/requests", response_model=list[AIRequestRecord])
def requests():
    return list(reversed(REQUESTS))


@app.post("/api/requests", response_model=AIRequestRecord)
def submit_request(request: AIRequestCreate):
    record = create_record(request)
    REQUESTS.append(record)
    return record


@app.get("/api/evidence/{request_id}", response_model=AIRequestRecord)
def evidence(request_id: str):
    for record in REQUESTS:
        if record.request_id == request_id:
            return record
    raise HTTPException(status_code=404, detail="Request not found")


@app.patch("/api/requests/{request_id}/approval", response_model=AIRequestRecord)
def review_request(request_id: str, action: ApprovalAction):
    for index, record in enumerate(REQUESTS):
        if record.request_id != request_id:
            continue

        next_status = {
            "approve": "approved",
            "reject": "rejected",
            "escalate": "escalated",
        }[action.action]

        updated_request = AIRequestCreate(
            user=record.user,
            role=record.role,
            department=record.department,
            clearance_level=record.clearance_level,
            business_purpose=record.business_purpose,
            request_type=record.request_type,
            prompt=record.prompt,
            data_classification=record.data_classification,
            tool_calls=record.tool_calls,
            approval_status=next_status,
            device_trust=record.device_trust,
            location_context=record.location_context,
        )

        result = evaluate_policy(updated_request)

        updated = AIRequestRecord(
            **updated_request.model_dump(),
            request_id=record.request_id,
            created_at=record.created_at,
            model=record.model,
            prompt_version=record.prompt_version,
            policy_result=result,
            final_outcome=result.decision.value,
            reviewer=action.reviewer,
            reviewer_action=action.action,
            reviewer_note=action.note,
            reviewed_at=now(),
        )

        REQUESTS[index] = updated
        return updated

    raise HTTPException(status_code=404, detail="Request not found")
