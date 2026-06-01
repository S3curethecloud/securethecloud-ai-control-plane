export type DashboardSummary = {
  total_requests: number;
  denied_requests: number;
  high_risk_requests: number;
  approval_required: number;
  redacted_requests: number;
  sensitive_data_attempts: number;
  policy_violations: number;
  human_approvals: number;
};

export type AIRequestRecord = {
  request_id: string;
  created_at: string;
  user: string;
  role: string;
  department: string;
  clearance_level: number;
  business_purpose: string;
  request_type: string;
  prompt: string;
  data_classification: string;
  tool_calls: string[];
  approval_status: string;
  model: string;
  prompt_version: string;
  final_outcome: string;
  policy_result: {
    decision: string;
    reason: string;
    risk_tier: string;
    redactions_required: boolean;
    human_approval_required: boolean;
    blocked_tool_calls: string[];
  };
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://backend:8000";

export async function fetchDashboard(): Promise<DashboardSummary> {
  const res = await fetch(`${API_BASE_URL}/api/dashboard`, { cache: "no-store" });
  if (!res.ok) throw new Error("Unable to load dashboard");
  return res.json();
}

export async function fetchRequests(): Promise<AIRequestRecord[]> {
  const res = await fetch(`${API_BASE_URL}/api/requests`, { cache: "no-store" });
  if (!res.ok) throw new Error("Unable to load requests");
  return res.json();
}
