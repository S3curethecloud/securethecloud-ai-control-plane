from pathlib import Path
import re

backend = Path("backend/app/main.py")
frontend = Path("frontend/app/page.tsx")

b = backend.read_text()
f = frontend.read_text()

# -------------------------
# Backend patch
# -------------------------

if "class ToolFirewallDecision" not in b:
    marker = '''class ApprovalAction(BaseModel):
    action: Literal["approve", "reject", "escalate"]
    reviewer: str = "Security Officer"
    note: str = "Reviewed in Phase 8 Human Approval Workspace"


app = FastAPI'''
    replacement = '''class ApprovalAction(BaseModel):
    action: Literal["approve", "reject", "escalate"]
    reviewer: str = "Security Officer"
    note: str = "Reviewed in Phase 8 Human Approval Workspace"


class ToolFirewallDecision(BaseModel):
    tool: ToolCall
    status: Literal["allowed", "blocked", "requires_approval", "redacted"]
    reason: str


app = FastAPI'''
    if marker not in b:
        raise SystemExit("Backend marker for ApprovalAction not found.")
    b = b.replace(marker, replacement)

pattern = r'''def blocked_tools_for\(request: AIRequestCreate\) -> list\[ToolCall\]:.*?\n\n\ndef evaluate_policy'''
replacement = '''def evaluate_tool_firewall(request: AIRequestCreate) -> list[ToolFirewallDecision]:
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


def evaluate_policy'''
b, count = re.subn(pattern, replacement, b, flags=re.S)
if count != 1:
    raise SystemExit(f"Backend blocked_tools_for replacement count was {count}, expected 1.")

if "/api/tool-firewall/preview" not in b:
    marker = '''@app.get("/health", response_model=Health)
def health():'''
    insert = '''@app.post("/api/tool-firewall/preview", response_model=list[ToolFirewallDecision])
def tool_firewall_preview(request: AIRequestCreate):
    return evaluate_tool_firewall(request)


@app.get("/health", response_model=Health)
def health():'''
    if marker not in b:
        raise SystemExit("Backend health endpoint marker not found.")
    b = b.replace(marker, insert)

backend.write_text(b)

# -------------------------
# Frontend patch
# -------------------------

if "type ToolFirewallDecision" not in f:
    marker = '''type Dashboard = {
  total_requests: number;
  denied_requests: number;
  high_risk_requests: number;
  approval_required: number;
  redacted_requests: number;
  sensitive_data_attempts: number;
  policy_violations: number;
  human_approvals: number;
};'''
    insert = '''type Dashboard = {
  total_requests: number;
  denied_requests: number;
  high_risk_requests: number;
  approval_required: number;
  redacted_requests: number;
  sensitive_data_attempts: number;
  policy_violations: number;
  human_approvals: number;
};

type ToolFirewallDecision = {
  tool: string;
  status: "allowed" | "blocked" | "requires_approval" | "redacted";
  reason: string;
};'''
    if marker not in f:
        raise SystemExit("Frontend Dashboard type marker not found.")
    f = f.replace(marker, insert)

f = f.replace(
    'tool_calls: ["search_documents", "access_records"],',
    'tool_calls: ["search_documents", "call_api", "access_records", "write_files", "trigger_workflow", "send_message"],'
)

if "const [firewall, setFirewall]" not in f:
    marker = '''  const [lastDecision, setLastDecision] = useState<RequestRecord | null>(null);
  const [reviewer, setReviewer] = useState("Security Officer");'''
    insert = '''  const [lastDecision, setLastDecision] = useState<RequestRecord | null>(null);
  const [reviewer, setReviewer] = useState("Security Officer");
  const [firewall, setFirewall] = useState<ToolFirewallDecision[]>([]);'''
    if marker not in f:
        raise SystemExit("Frontend state marker not found.")
    f = f.replace(marker, insert)

if "async function loadFirewall" not in f:
    marker = '''  async function loadData() {
    const [dashboardRes, requestsRes] = await Promise.all([
      fetch(`${API_BASE}/api/dashboard`, { cache: "no-store" }),
      fetch(`${API_BASE}/api/requests`, { cache: "no-store" }),
    ]);

    setDashboard(await dashboardRes.json());
    setRequests(await requestsRes.json());
  }'''
    insert = '''  async function loadData() {
    const [dashboardRes, requestsRes] = await Promise.all([
      fetch(`${API_BASE}/api/dashboard`, { cache: "no-store" }),
      fetch(`${API_BASE}/api/requests`, { cache: "no-store" }),
    ]);

    setDashboard(await dashboardRes.json());
    setRequests(await requestsRes.json());
  }

  async function loadFirewall() {
    const res = await fetch(`${API_BASE}/api/tool-firewall/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });

    if (res.ok) {
      setFirewall(await res.json());
    }
  }'''
    if marker not in f:
        raise SystemExit("Frontend loadData marker not found.")
    f = f.replace(marker, insert)

if "loadFirewall().catch" not in f:
    marker = '''  useEffect(() => {
    loadData().catch((err) => setStatus(`Load failed: ${err.message}`));
  }, []);'''
    insert = '''  useEffect(() => {
    loadData().catch((err) => setStatus(`Load failed: ${err.message}`));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadFirewall().catch(() => undefined);
    }, 200);

    return () => clearTimeout(timer);
  }, [form]);'''
    if marker not in f:
        raise SystemExit("Frontend useEffect marker not found.")
    f = f.replace(marker, insert)

if "AI Tool-Call Firewall Console" not in f:
    marker = '''        <section style={styles.workspaceThree}>'''
    insert = '''        <section style={styles.firewallConsole}>
          <div style={styles.firewallHeader}>
            <div>
              <p style={styles.kicker}>Phase 9</p>
              <h2 style={styles.sectionTitleLeft}>AI Tool-Call Firewall Console</h2>
              <p style={styles.sectionSubLeft}>
                Requested AI tools are evaluated before execution. Sensitive tools are blocked or routed to approval until policy, identity, and evidence checks pass.
              </p>
            </div>
            <div style={styles.firewallDoctrine}>
              AI can reason and recommend. AI cannot invoke tools until policy, approval, and evidence checks pass.
            </div>
          </div>

          <div style={styles.firewallGrid}>
            {firewall.length === 0 && (
              <div style={styles.empty}>Select requested tool calls to preview firewall decisions.</div>
            )}

            {firewall.map((item) => (
              <article key={item.tool} style={styles.firewallCard}>
                <div style={styles.recordHead}>
                  <strong>{item.tool}</strong>
                  <span style={{ ...styles.firewallPill, ...firewallTone(item.status) }}>
                    {item.status.replace("_", " ").toUpperCase()}
                  </span>
                </div>
                <p>{item.reason}</p>
              </article>
            ))}
          </div>
        </section>

        <section style={styles.workspaceThree}>'''
    if marker not in f:
        raise SystemExit("Frontend workspace marker not found.")
    f = f.replace(marker, insert)

if "function firewallTone" not in f:
    marker = '''function token(color: string) {'''
    insert = '''function firewallTone(status: string): CSSProperties {
  if (status === "allowed") {
    return { borderColor: "#22c55e", color: "#86efac", background: "rgba(20,83,45,.45)" };
  }

  if (status === "blocked") {
    return { borderColor: "#ef4444", color: "#fca5a5", background: "rgba(127,29,29,.42)" };
  }

  if (status === "requires_approval") {
    return { borderColor: "#f59e0b", color: "#fcd34d", background: "rgba(69,26,3,.45)" };
  }

  return { borderColor: "#38bdf8", color: "#bae6fd", background: "rgba(8,47,73,.45)" };
}

function token(color: string) {'''
    if marker not in f:
        raise SystemExit("Frontend token function marker not found.")
    f = f.replace(marker, insert)

if "firewallConsole:" not in f:
    marker = '''  metric: { border: "1px solid #334155", borderRadius: 18, padding: 18, background: "rgba(15,23,42,.8)", display: "grid", gap: 6 },
  workspaceThree:'''
    insert = '''  metric: { border: "1px solid #334155", borderRadius: 18, padding: 18, background: "rgba(15,23,42,.8)", display: "grid", gap: 6 },
  firewallConsole: { marginTop: 18, border: "1px solid #475569", borderRadius: 22, padding: 22, background: "rgba(2,6,23,.62)" },
  firewallHeader: { display: "flex", justifyContent: "space-between", gap: 18, alignItems: "stretch" },
  firewallDoctrine: { maxWidth: 360, border: "1px solid #e879f9", borderRadius: 16, padding: 18, color: "#f5d0fe", background: "rgba(88,28,135,.22)", fontWeight: 800 },
  firewallGrid: { display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14, marginTop: 18 },
  firewallCard: { border: "1px solid #334155", borderRadius: 16, padding: 16, background: "#020617", minHeight: 128 },
  firewallPill: { border: "1px solid", borderRadius: 999, padding: "7px 10px", fontSize: 11, fontWeight: 900, whiteSpace: "nowrap" },
  workspaceThree:'''
    if marker not in f:
        raise SystemExit("Frontend style marker not found.")
    f = f.replace(marker, insert)

frontend.write_text(f)
print("Phase 9 patch applied successfully.")
