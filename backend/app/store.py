from datetime import datetime
from uuid import uuid4
from .models import AIRequestCreate, AIRequestRecord, DashboardSummary
from .policy import evaluate_policy

REQUESTS: list[AIRequestRecord] = []


def seed() -> None:
    if REQUESTS:
        return
    examples = [
        AIRequestCreate(user="Avery Chen", role="Risk Analyst", department="Finance", clearance_level=4, business_purpose="Quarterly risk review for executive reporting", request_type="Generate executive risk report", prompt="Summarize restricted loan exposure trends", data_classification="restricted", tool_calls=["access_records"], approval_status="approved"),
        AIRequestCreate(user="Mina Patel", role="Care Coordinator", department="Healthcare", clearance_level=3, business_purpose="Prepare patient care follow-up summary", request_type="Review healthcare notes", prompt="Summarize patient notes", data_classification="regulated", tool_calls=["access_records"], approval_status="not_requested"),
        AIRequestCreate(user="Jordan Lee", role="Engineer", department="IT", clearance_level=2, business_purpose="Investigate application security event", request_type="Analyze security logs", prompt="Analyze internal logs for anomalies", data_classification="confidential", tool_calls=["search_documents"]),
    ]
    for item in examples:
        create_request(item)


def create_request(payload: AIRequestCreate) -> AIRequestRecord:
    result = evaluate_policy(payload)
    record = AIRequestRecord(
        **payload.model_dump(),
        request_id=f"req_{uuid4().hex[:10]}",
        created_at=datetime.utcnow(),
        policy_result=result,
        final_outcome=result.decision.value,
    )
    REQUESTS.insert(0, record)
    return record


def list_requests() -> list[AIRequestRecord]:
    seed()
    return REQUESTS


def get_request(request_id: str) -> AIRequestRecord | None:
    seed()
    return next((r for r in REQUESTS if r.request_id == request_id), None)


def dashboard_summary() -> DashboardSummary:
    seed()
    total = len(REQUESTS)
    return DashboardSummary(
        total_requests=total,
        denied_requests=sum(1 for r in REQUESTS if r.policy_result.decision == "deny"),
        high_risk_requests=sum(1 for r in REQUESTS if r.policy_result.risk_tier in {"high", "critical"}),
        approval_required=sum(1 for r in REQUESTS if r.policy_result.human_approval_required),
        redacted_requests=sum(1 for r in REQUESTS if r.policy_result.redactions_required),
        sensitive_data_attempts=sum(1 for r in REQUESTS if r.data_classification in {"confidential", "regulated", "restricted"}),
        policy_violations=sum(1 for r in REQUESTS if r.policy_result.decision in {"deny", "require_approval"}),
        human_approvals=sum(1 for r in REQUESTS if r.approval_status == "approved"),
    )
