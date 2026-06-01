package securethecloud.ai_control_plane

# OPA/Rego-style policy reference for the lab.
# Local execution uses backend/app/policy.py so the demo has no OPA runtime dependency.

default allow := false

sensitive_data := {"confidential", "regulated", "restricted"}
high_risk_data := {"regulated", "restricted"}
mutating_tools := {"write_files", "trigger_workflow", "send_message"}

allow if {
  input.business_purpose != ""
  input.device_trust == "trusted"
  input.location_context == "corporate"
  not high_risk_data[input.data_classification]
}

require_approval if {
  high_risk_data[input.data_classification]
  input.approval_status != "approved"
}

deny if {
  high_risk_data[input.data_classification]
  input.clearance_level < 4
}

deny if {
  input.device_trust != "trusted"
}

redact if {
  input.data_classification == "confidential"
}
