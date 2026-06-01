from .models import AIRequestCreate, PolicyResult, PolicyDecision, DataClassification, ToolCall

HIGH_RISK_DATA = {DataClassification.regulated, DataClassification.restricted}
SENSITIVE_DATA = {DataClassification.confidential, DataClassification.regulated, DataClassification.restricted}
MUTATING_TOOLS = {ToolCall.write_files, ToolCall.trigger_workflow, ToolCall.send_message}
RECORD_TOOLS = {ToolCall.access_records, ToolCall.call_api, ToolCall.search_documents}


def evaluate_policy(req: AIRequestCreate) -> PolicyResult:
    blocked = []

    if not req.business_purpose or len(req.business_purpose.strip()) < 8:
        return PolicyResult(
            decision=PolicyDecision.deny,
            reason="Business purpose is missing or insufficient for governed AI access.",
            risk_tier="high",
            blocked_tool_calls=req.tool_calls,
        )

    if req.device_trust != "trusted":
        return PolicyResult(
            decision=PolicyDecision.deny,
            reason="Device trust failed; sensitive AI workflow access is blocked.",
            risk_tier="high",
            blocked_tool_calls=req.tool_calls,
        )

    if req.location_context not in {"corporate", "approved_remote"}:
        return PolicyResult(
            decision=PolicyDecision.deny,
            reason="Location context is not approved for regulated data workflows.",
            risk_tier="high",
            blocked_tool_calls=req.tool_calls,
        )

    if req.data_classification in HIGH_RISK_DATA and req.clearance_level < 4:
        return PolicyResult(
            decision=PolicyDecision.deny,
            reason="Clearance level is too low for regulated or restricted data.",
            risk_tier="critical",
            blocked_tool_calls=req.tool_calls,
        )

    for tool in req.tool_calls:
        if tool in MUTATING_TOOLS:
            blocked.append(tool)
        if req.data_classification in HIGH_RISK_DATA and tool in RECORD_TOOLS and req.approval_status != "approved":
            blocked.append(tool)

    if blocked:
        return PolicyResult(
            decision=PolicyDecision.require_approval,
            reason="Requested tool calls touch sensitive workflows and require human approval.",
            risk_tier="high",
            human_approval_required=True,
            blocked_tool_calls=sorted(set(blocked)),
        )

    if req.data_classification == DataClassification.confidential:
        return PolicyResult(
            decision=PolicyDecision.redact,
            reason="Confidential data may be summarized only with redaction and evidence capture.",
            risk_tier="medium",
            redactions_required=True,
        )

    if req.data_classification in HIGH_RISK_DATA and req.approval_status == "approved":
        return PolicyResult(
            decision=PolicyDecision.allow,
            reason="High-risk request has sufficient identity context and approval evidence.",
            risk_tier="high",
        )

    return PolicyResult(
        decision=PolicyDecision.allow,
        reason="Request satisfies lab identity, purpose, classification, and tool-call controls.",
        risk_tier="low" if req.data_classification in {DataClassification.public, DataClassification.internal} else "medium",
    )
