"use client";

import { useEffect, useMemo, useState } from "react";
import type { CSSProperties, FormEvent } from "react";

const API_BASE = "http://localhost:8000";

type RequestRecord = {
  request_id: string;
  user: string;
  role: string;
  department: string;
  clearance_level: number;
  business_purpose: string;
  request_type: string;
  prompt: string;
  data_classification: string;
  tool_calls?: string[];
  approval_status: string;
  reviewer?: string | null;
  reviewer_action?: string | null;
  reviewer_note?: string | null;
  policy_result: {
    decision: string;
    reason: string;
    risk_tier: string;
    human_approval_required?: boolean;
    redactions_required?: boolean;
    blocked_tool_calls?: string[];
  };
};

type Dashboard = {
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
};

const initialForm = {
  user: "Taylor Morgan",
  role: "Analyst",
  department: "Finance",
  clearance_level: 4,
  business_purpose: "Quarterly risk review",
  request_type: "Summarize sensitive records",
  prompt: "Summarize restricted financial customer records for executive review.",
  data_classification: "restricted",
  tool_calls: ["search_documents", "call_api", "access_records", "write_files", "trigger_workflow", "send_message"],
  approval_status: "not_requested",
  device_trust: "trusted",
  location_context: "corporate",
};

const fabricModules = [
  ["Governance & Policy", "Policy decisioning, doctrine, access gates", "cyan"],
  ["Evidence & Audit", "Replayable request evidence and audit trail", "green"],
  ["Risk Intelligence", "Risk-tiering for AI workflow decisions", "blue"],
  ["Identity / Context", "Role, clearance, purpose, device, location", "amber"],
  ["Tool-Call Firewall", "Controls APIs, records, files, messages, workflows", "pink"],
];

const pipelineSteps = [
  ["request", "AI Request", "Request captured"],
  ["identity", "Identity Context", "Role, clearance, department, purpose checked"],
  ["classification", "Data Classification", "Sensitivity level evaluated"],
  ["policy", "Policy Engine", "Policy decision calculated"],
  ["firewall", "Tool Firewall", "Tool calls inspected"],
  ["approval", "Approval Gate", "Human approval requirement evaluated"],
  ["evidence", "Evidence Capture", "Audit record written"],
  ["decision", "Final Decision", "Governed outcome returned"],
];

const toolOptions = [
  "search_documents",
  "call_api",
  "access_records",
  "write_files",
  "trigger_workflow",
  "send_message",
];

export default function Home() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [requests, setRequests] = useState<RequestRecord[]>([]);
  const [form, setForm] = useState(initialForm);
  const [status, setStatus] = useState("");
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [lastDecision, setLastDecision] = useState<RequestRecord | null>(null);
  const [reviewer, setReviewer] = useState("Security Officer");
  const [firewall, setFirewall] = useState<ToolFirewallDecision[]>([]);

  const pendingApprovals = useMemo(
    () => requests.filter((r) => r.policy_result.decision === "require_approval"),
    [requests]
  );

  const executiveRisk = useMemo(() => {
    const risk = { low: 0, medium: 0, high: 0, critical: 0 };
    const decisions = {
      allow: 0,
      deny: 0,
      require_approval: 0,
      redact: 0,
      escalate: 0,
    };

    const toolSummary = {
      allowed: firewall.filter((item) => item.status === "allowed").length,
      blocked: firewall.filter((item) => item.status === "blocked").length,
      requiresApproval: firewall.filter((item) => item.status === "requires_approval").length,
      redacted: firewall.filter((item) => item.status === "redacted").length,
    };

    for (const request of requests) {
      const tier = request.policy_result.risk_tier as keyof typeof risk;
      const decision = request.policy_result.decision as keyof typeof decisions;

      if (tier in risk) {
        risk[tier] += 1;
      }

      if (decision in decisions) {
        decisions[decision] += 1;
      }
    }

    const sensitiveAttempts = requests.filter((request) =>
      ["confidential", "regulated", "restricted"].includes(request.data_classification)
    ).length;

    const posture =
      pendingApprovals.length > 0
        ? "Review Required"
        : decisions.deny > 0 || decisions.escalate > 0
          ? "Guarded"
          : "Demo Ready";

    return {
      risk,
      decisions,
      toolSummary,
      sensitiveAttempts,
      posture,
    };
  }, [requests, firewall, pendingApprovals.length]);

  async function loadData() {
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
  }

  useEffect(() => {
    loadData().catch((err) => setStatus(`Load failed: ${err.message}`));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadFirewall().catch(() => undefined);
    }, 200);

    return () => clearTimeout(timer);
  }, [form]);

  function markStep(step: string) {
    setActiveStep(step);
    setCompletedSteps((prev) => (prev.includes(step) ? prev : [...prev, step]));
  }

  function sleep(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function submitRequest(e: FormEvent) {
    e.preventDefault();

    setStatus("Running governed AI decision pipeline...");
    setCompletedSteps([]);
    setLastDecision(null);

    for (const [step] of pipelineSteps) {
      markStep(step);
      await sleep(140);

      if (step === "approval") {
        break;
      }
    }

    const res = await fetch(`${API_BASE}/api/requests`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });

    if (!res.ok) {
      setStatus(`Submit failed: ${res.status}`);
      setActiveStep(null);
      return;
    }

    const created = await res.json();

    markStep("evidence");
    await sleep(140);
    markStep("decision");

    setLastDecision(created);
    setStatus(`Decision recorded: ${created.policy_result.decision.toUpperCase()} / ${created.policy_result.risk_tier}`);

    await loadData();
  }

  async function reviewRequest(requestId: string, action: "approve" | "reject" | "escalate") {
    setStatus(`${action.toUpperCase()} review submitted for ${requestId}...`);

    const res = await fetch(`${API_BASE}/api/requests/${requestId}/approval`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        reviewer,
        note: `Phase 8 reviewer action: ${action}`,
      }),
    });

    if (!res.ok) {
      setStatus(`Review failed: ${res.status}`);
      return;
    }

    const updated = await res.json();
    setLastDecision(updated);
    setStatus(`Human review complete: ${action.toUpperCase()} → ${updated.policy_result.decision.toUpperCase()}`);
    await loadData();
  }

  function toggleTool(tool: string) {
    const current = form.tool_calls;
    const next = current.includes(tool)
      ? current.filter((item) => item !== tool)
      : [...current, tool];

    setForm({ ...form, tool_calls: next });
  }

  return (
    <main style={styles.page}>
      <section style={styles.shell}>
        <header style={styles.hero}>
          <div>
            <div style={styles.brand}>🛡️ SecureTheCloud</div>
            <p style={styles.kicker}>Recommended Lab</p>
            <h1 style={styles.title}>SecureTheCloud AI Control Plane</h1>
            <p style={styles.subtitle}>
              A governed AI access, policy, approval, and evidence platform for regulated enterprise workflows.
            </p>
          </div>

          <div style={styles.principles}>
            <strong>Portfolio Principles</strong>
            <span>✓ Modular, not monolithic</span>
            <span>✓ Evidence-first governance</span>
            <span>✓ Deterministic policy gates</span>
            <span>✓ Human approval before sensitive action</span>
            <span>✓ Audit-ready workflow replay</span>
          </div>
        </header>

        <section style={styles.fabric}>
          <h2 style={styles.sectionTitle}>Shared Trust Fabric</h2>
          <p style={styles.sectionSub}>Common governance services for AI workflow control.</p>

          <div style={styles.moduleRow}>
            {fabricModules.map(([name, desc, color]) => (
              <div key={name} style={{ ...styles.fabricCard, borderColor: token(color) }}>
                <div style={{ ...styles.icon, color: token(color) }}>⬡</div>
                <strong>{name}</strong>
                <span>{desc}</span>
              </div>
            ))}
          </div>
        </section>

        <section style={styles.pipeline}>
          <div style={styles.pipelineHeader}>
            <div>
              <p style={styles.kicker}>Phase 8</p>
              <h2 style={styles.sectionTitleLeft}>Governed AI Decision Pipeline</h2>
              <p style={styles.sectionSubLeft}>
                AI request decisions now include a human approval workspace for restricted and regulated workflows.
              </p>
            </div>

            <div style={styles.pipelineDecision}>
              <span>Latest Outcome</span>
              <strong>{lastDecision ? lastDecision.policy_result.decision.toUpperCase() : "WAITING"}</strong>
              <small>{lastDecision ? `Risk: ${lastDecision.policy_result.risk_tier}` : "Submit or review a request"}</small>
            </div>
          </div>

          <div style={styles.pipelineGrid}>
            {pipelineSteps.map(([id, title, desc], index) => {
              const complete = completedSteps.includes(id);
              const active = activeStep === id;

              return (
                <div
                  key={id}
                  style={{
                    ...styles.pipelineStep,
                    borderColor: active ? "#22d3ee" : complete ? "#6ee75f" : "#334155",
                    boxShadow: active ? "0 0 28px rgba(34,211,238,.35)" : "none",
                  }}
                >
                  <div style={styles.stepNumber}>{index + 1}</div>
                  <strong>{title}</strong>
                  <p>{desc}</p>
                  <span
                    style={{
                      ...styles.stepStatus,
                      color: complete ? "#86efac" : "#94a3b8",
                      borderColor: complete ? "#6ee75f" : "#334155",
                    }}
                  >
                    {active ? "Running" : complete ? "Complete" : "Queued"}
                  </span>
                </div>
              );
            })}
          </div>
        </section>

        {dashboard && (
          <section style={styles.metrics}>
            <Metric label="AI Requests" value={dashboard.total_requests} />
            <Metric label="Denied" value={dashboard.denied_requests} />
            <Metric label="High Risk" value={dashboard.high_risk_requests} />
            <Metric label="Approval Gates" value={dashboard.approval_required} />
            <Metric label="Human Approvals" value={dashboard.human_approvals} />
            <Metric label="Policy Violations" value={dashboard.policy_violations} />
          </section>
        )}

        <section style={styles.executiveCenter}>
          <div style={styles.executiveHeader}>
            <div>
              <p style={styles.kicker}>Phase 10</p>
              <h2 style={styles.sectionTitleLeft}>Executive Risk Center</h2>
              <p style={styles.sectionSubLeft}>
                Leadership view of AI governance posture across risk, policy decisions, approval health, sensitive access, and tool-call firewall activity.
              </p>
            </div>

            <div style={styles.postureCard}>
              <span>Executive Readiness Posture</span>
              <strong>{executiveRisk.posture}</strong>
              <small>
                {pendingApprovals.length > 0
                  ? "Human review queue requires attention"
                  : "Current governed workflow evidence is reviewable"}
              </small>
            </div>
          </div>

          <div style={styles.executiveGrid}>
            <div style={styles.execPanel}>
              <h3>Risk Distribution</h3>
              <RiskBar label="Low" value={executiveRisk.risk.low} max={Math.max(1, requests.length)} tone="#22c55e" />
              <RiskBar label="Medium" value={executiveRisk.risk.medium} max={Math.max(1, requests.length)} tone="#38bdf8" />
              <RiskBar label="High" value={executiveRisk.risk.high} max={Math.max(1, requests.length)} tone="#f59e0b" />
              <RiskBar label="Critical" value={executiveRisk.risk.critical} max={Math.max(1, requests.length)} tone="#ef4444" />
            </div>

            <div style={styles.execPanel}>
              <h3>Decision Distribution</h3>
              <MiniStat label="Allowed" value={executiveRisk.decisions.allow} />
              <MiniStat label="Denied" value={executiveRisk.decisions.deny} />
              <MiniStat label="Requires Approval" value={executiveRisk.decisions.require_approval} />
              <MiniStat label="Redacted" value={executiveRisk.decisions.redact} />
              <MiniStat label="Escalated" value={executiveRisk.decisions.escalate} />
            </div>

            <div style={styles.execPanel}>
              <h3>Tool-Call Firewall Summary</h3>
              <MiniStat label="Allowed tools" value={executiveRisk.toolSummary.allowed} />
              <MiniStat label="Blocked tools" value={executiveRisk.toolSummary.blocked} />
              <MiniStat label="Requires approval" value={executiveRisk.toolSummary.requiresApproval} />
              <MiniStat label="Redacted tools" value={executiveRisk.toolSummary.redacted} />
            </div>

            <div style={styles.execPanel}>
              <h3>Governance Health</h3>
              <MiniStat label="Pending approvals" value={pendingApprovals.length} />
              <MiniStat label="Sensitive attempts" value={executiveRisk.sensitiveAttempts} />
              <MiniStat label="Policy violations" value={dashboard?.policy_violations ?? 0} />
              <MiniStat label="Human approvals" value={dashboard?.human_approvals ?? 0} />
            </div>
          </div>
        </section>

        <section style={styles.workspaceFour}>
          <form onSubmit={submitRequest} style={styles.panel}>
            <p style={styles.kicker}>AI Access Portal</p>
            <h2 style={styles.panelTitle}>Submit Governed AI Request</h2>
            <p style={styles.muted}>Restricted or regulated requests can now route to human approval.</p>

            <Input label="User" value={form.user} onChange={(v) => setForm({ ...form, user: v })} />
            <Input label="Role" value={form.role} onChange={(v) => setForm({ ...form, role: v })} />
            <Input label="Department" value={form.department} onChange={(v) => setForm({ ...form, department: v })} />
            <Input label="Business Purpose" value={form.business_purpose} onChange={(v) => setForm({ ...form, business_purpose: v })} />
            <Input label="Request Type" value={form.request_type} onChange={(v) => setForm({ ...form, request_type: v })} />

            <label style={styles.label}>Clearance Level</label>
            <select
              style={styles.input}
              value={form.clearance_level}
              onChange={(e) => setForm({ ...form, clearance_level: Number(e.target.value) })}
            >
              <option value={0}>0 - No clearance</option>
              <option value={1}>1 - Basic</option>
              <option value={2}>2 - Internal</option>
              <option value={3}>3 - Confidential</option>
              <option value={4}>4 - Regulated</option>
              <option value={5}>5 - Restricted</option>
            </select>

            <label style={styles.label}>Data Classification</label>
            <select
              style={styles.input}
              value={form.data_classification}
              onChange={(e) => setForm({ ...form, data_classification: e.target.value })}
            >
              <option value="public">public</option>
              <option value="internal">internal</option>
              <option value="confidential">confidential</option>
              <option value="regulated">regulated</option>
              <option value="restricted">restricted</option>
            </select>

            <label style={styles.label}>Requested AI Tool Calls</label>
            <div style={styles.toolGrid}>
              {toolOptions.map((tool) => (
                <label key={tool} style={styles.toolOption}>
                  <input type="checkbox" checked={form.tool_calls.includes(tool)} onChange={() => toggleTool(tool)} />
                  <span>{tool}</span>
                </label>
              ))}
            </div>

            <label style={styles.label}>Prompt</label>
            <textarea
              style={{ ...styles.input, minHeight: 90 }}
              value={form.prompt}
              onChange={(e) => setForm({ ...form, prompt: e.target.value })}
            />

            <button style={styles.button}>Run Governed Decision Pipeline</button>
            {status && <p style={styles.status}>{status}</p>}
          </form>

          <div style={styles.panel}>
            <p style={styles.kicker}>Tool-Call Firewall</p>
            <h2 style={styles.panelTitle}>AI Tool Console</h2>
            <p style={styles.muted}>
              Each requested AI tool is evaluated before execution.
            </p>

            <div style={styles.firewallDoctrineCompact}>
              AI can reason and recommend. AI cannot invoke tools until policy, approval, and evidence checks pass.
            </div>

            <div style={styles.feed}>
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
          </div>

          <div style={styles.panel}>
            <p style={styles.kicker}>Human Approval Workspace</p>
            <h2 style={styles.panelTitle}>Pending Approvals</h2>
            <p style={styles.muted}>Approve, reject, or escalate sensitive AI requests before access is allowed.</p>

            <label style={styles.label}>Reviewer</label>
            <select style={styles.input} value={reviewer} onChange={(e) => setReviewer(e.target.value)}>
              <option>Security Officer</option>
              <option>Compliance Officer</option>
              <option>Data Steward</option>
              <option>Risk Executive</option>
            </select>

            <div style={styles.feed}>
              {pendingApprovals.length === 0 && (
                <div style={styles.empty}>No pending approval requests.</div>
              )}

              {pendingApprovals.map((req) => (
                <article key={req.request_id} style={styles.approvalCard}>
                  <div style={styles.recordHead}>
                    <div>
                      <strong>{req.request_type}</strong>
                      <p>{req.request_id}</p>
                    </div>
                    <span style={styles.approvalBadge}>APPROVAL REQUIRED</span>
                  </div>

                  <p>{req.user} · {req.role} · {req.department}</p>
                  <p>Classification: <b>{req.data_classification}</b> · Risk: <b>{req.policy_result.risk_tier}</b></p>
                  <p>{req.policy_result.reason}</p>

                  {req.policy_result.blocked_tool_calls && req.policy_result.blocked_tool_calls.length > 0 && (
                    <p style={styles.blocked}>Blocked until review: {req.policy_result.blocked_tool_calls.join(", ")}</p>
                  )}

                  <div style={styles.reviewActions}>
                    <button type="button" style={styles.approveButton} onClick={() => reviewRequest(req.request_id, "approve")}>
                      Approve
                    </button>
                    <button type="button" style={styles.rejectButton} onClick={() => reviewRequest(req.request_id, "reject")}>
                      Reject
                    </button>
                    <button type="button" style={styles.escalateButton} onClick={() => reviewRequest(req.request_id, "escalate")}>
                      Escalate
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div style={styles.panel}>
            <p style={styles.kicker}>Evidence Replay</p>
            <h2 style={styles.panelTitle}>Latest Decisions</h2>

            <div style={styles.feed}>
              {requests.map((req) => (
                <article key={req.request_id} style={styles.record}>
                  <div style={styles.recordHead}>
                    <div>
                      <strong>{req.request_type}</strong>
                      <p>{req.request_id}</p>
                    </div>
                    <span style={styles.badge}>{req.policy_result.decision.toUpperCase()}</span>
                  </div>

                  <p>{req.user} · {req.role} · {req.department}</p>
                  <p>Classification: <b>{req.data_classification}</b> · Risk: <b>{req.policy_result.risk_tier}</b></p>
                  <p>{req.policy_result.reason}</p>

                  {req.reviewer_action && (
                    <p style={styles.reviewEvidence}>
                      Reviewer: {req.reviewer} · Action: {req.reviewer_action.toUpperCase()}
                    </p>
                  )}

                  {req.policy_result.blocked_tool_calls && req.policy_result.blocked_tool_calls.length > 0 && (
                    <p style={styles.blocked}>Blocked tools: {req.policy_result.blocked_tool_calls.join(", ")}</p>
                  )}
                </article>
              ))}
            </div>
          </div>
        </section>

        <footer style={styles.footer}>
          AI may assist · Policy decides · Human approval gates sensitive action · Evidence proves what happened
        </footer>
      </section>
    </main>
  );
}

function RiskBar({ label, value, max, tone }: { label: string; value: number; max: number; tone: string }) {
  const width = `${Math.min(100, Math.round((value / max) * 100))}%`;

  return (
    <div style={styles.riskRow}>
      <div style={styles.riskLabel}>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <div style={styles.riskTrack}>
        <div style={{ ...styles.riskFill, width, background: tone }} />
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div style={styles.miniStat}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div style={styles.metric}>
      <strong style={{ fontSize: 28, lineHeight: 1 }}>{value}</strong>
      <span style={{ color: "#cbd5e1", fontSize: 13 }}>{label}</span>
    </div>
  );
}

function Input({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <>
      <label style={styles.label}>{label}</label>
      <input style={styles.input} value={value} onChange={(e) => onChange(e.target.value)} />
    </>
  );
}

function firewallTone(status: string): CSSProperties {
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

function token(color: string) {
  const map: Record<string, string> = {
    cyan: "#22d3ee",
    green: "#6ee75f",
    blue: "#38bdf8",
    amber: "#f59e0b",
    pink: "#e879f9",
  };
  return map[color] ?? "#22d3ee";
}

const styles: Record<string, CSSProperties> = {
  page: { minHeight: "100vh", background: "radial-gradient(circle at top left,#132b46,#06111f 45%,#020617)", color: "#eaf2ff", fontFamily: "Inter, Arial, sans-serif", padding: 28 },
  shell: { maxWidth: 1480, margin: "0 auto" },
  hero: { border: "1px solid #334155", borderRadius: 24, padding: 34, display: "flex", justifyContent: "space-between", gap: 24, background: "rgba(15,23,42,.78)", boxShadow: "0 24px 80px rgba(0,0,0,.35)" },
  brand: { fontSize: 24, fontWeight: 900, color: "#facc15", marginBottom: 18 },
  kicker: { color: "#67e8f9", textTransform: "uppercase", letterSpacing: 2, fontSize: 12, fontWeight: 800 },
  title: { fontSize: 60, lineHeight: .95, margin: "10px 0", fontWeight: 950 },
  subtitle: { color: "#cbd5e1", fontSize: 18 },
  principles: { border: "1px solid #94a3b8", borderRadius: 16, padding: 18, minWidth: 310, display: "grid", gap: 10, background: "rgba(2,6,23,.6)" },
  fabric: { marginTop: 18, border: "1px solid #475569", borderRadius: 22, padding: 22, background: "rgba(2,6,23,.6)" },
  sectionTitle: { textAlign: "center", textTransform: "uppercase", letterSpacing: 5, fontSize: 24, margin: 0 },
  sectionTitleLeft: { textTransform: "uppercase", letterSpacing: 4, fontSize: 24, margin: "4px 0" },
  sectionSub: { textAlign: "center", color: "#cbd5e1", marginTop: 6 },
  sectionSubLeft: { color: "#cbd5e1", marginTop: 6, maxWidth: 780 },
  moduleRow: { display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 16, marginTop: 18 },
  fabricCard: { border: "2px solid", borderRadius: 12, padding: 18, background: "linear-gradient(135deg,rgba(8,47,73,.55),rgba(2,6,23,.8))", minHeight: 120, display: "grid", gap: 8 },
  icon: { fontSize: 34 },
  pipeline: { marginTop: 18, border: "1px solid #475569", borderRadius: 22, padding: 22, background: "linear-gradient(135deg,rgba(15,23,42,.88),rgba(2,6,23,.72))" },
  pipelineHeader: { display: "flex", justifyContent: "space-between", gap: 18, alignItems: "stretch" },
  pipelineDecision: { minWidth: 260, border: "1px solid #22d3ee", borderRadius: 16, padding: 18, background: "rgba(8,47,73,.5)", display: "grid", gap: 8 },
  pipelineGrid: { display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginTop: 18 },
  pipelineStep: { border: "1px solid", borderRadius: 16, padding: 16, background: "#020617", minHeight: 145, transition: "all .2s ease" },
  stepNumber: { width: 32, height: 32, borderRadius: 999, background: "#0c4a6e", color: "#a5f3fc", display: "grid", placeItems: "center", fontWeight: 900, marginBottom: 10 },
  stepStatus: { display: "inline-block", border: "1px solid", borderRadius: 999, padding: "4px 10px", fontSize: 12, fontWeight: 900, marginTop: 8 },
  metrics: { display: "grid", gridTemplateColumns: "repeat(6,1fr)", gap: 14, marginTop: 18 },
  executiveCenter: { marginTop: 18, border: "1px solid #475569", borderRadius: 22, padding: 22, background: "linear-gradient(135deg,rgba(15,23,42,.9),rgba(2,6,23,.72))" },
  executiveHeader: { display: "flex", justifyContent: "space-between", gap: 18, alignItems: "stretch" },
  postureCard: { minWidth: 300, border: "1px solid #6ee75f", borderRadius: 16, padding: 18, background: "rgba(20,83,45,.22)", display: "grid", gap: 8 },
  executiveGrid: { display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr 1fr", gap: 14, marginTop: 18 },
  execPanel: { border: "1px solid #334155", borderRadius: 16, padding: 16, background: "#020617" },
  riskRow: { display: "grid", gap: 6, marginTop: 12 },
  riskLabel: { display: "flex", justifyContent: "space-between", color: "#cbd5e1", fontSize: 13 },
  riskTrack: { height: 10, borderRadius: 999, background: "#0f172a", overflow: "hidden", border: "1px solid #334155" },
  riskFill: { height: "100%", borderRadius: 999 },
  miniStat: { display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid #1e293b", paddingTop: 10, marginTop: 10, color: "#cbd5e1" },
  metric: { border: "1px solid #334155", borderRadius: 18, padding: 18, background: "rgba(15,23,42,.8)", display: "grid", gap: 6 },
  firewallConsole: { marginTop: 18, border: "1px solid #475569", borderRadius: 22, padding: 22, background: "rgba(2,6,23,.62)" },
  firewallHeader: { display: "flex", justifyContent: "space-between", gap: 18, alignItems: "stretch" },
  firewallDoctrine: { maxWidth: 360, border: "1px solid #e879f9", borderRadius: 16, padding: 18, color: "#f5d0fe", background: "rgba(88,28,135,.22)", fontWeight: 800 },
  firewallGrid: { display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14, marginTop: 18 },
  firewallCard: { border: "1px solid #334155", borderRadius: 16, padding: 16, background: "#020617", minHeight: 128 },
  firewallPill: { border: "1px solid", borderRadius: 999, padding: "7px 10px", fontSize: 11, fontWeight: 900, whiteSpace: "nowrap" },
  workspaceThree: { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 18, marginTop: 18 },
  workspaceFour: { display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 18, marginTop: 18 },
  panel: { border: "1px solid #334155", borderRadius: 22, padding: 24, background: "rgba(15,23,42,.86)" },
  panelTitle: { fontSize: 26, margin: "8px 0" },
  muted: { color: "#cbd5e1" },
  label: { display: "block", marginTop: 12, marginBottom: 5, color: "#cbd5e1", fontSize: 13, fontWeight: 700 },
  input: { width: "100%", boxSizing: "border-box", borderRadius: 12, border: "1px solid #475569", background: "#020617", color: "#eaf2ff", padding: 12 },
  toolGrid: { display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 8 },
  toolOption: { border: "1px solid #334155", borderRadius: 12, padding: 10, background: "#020617", display: "flex", gap: 8, alignItems: "center", fontSize: 13 },
  button: { marginTop: 16, width: "100%", border: 0, borderRadius: 12, background: "#22d3ee", color: "#020617", padding: 14, fontWeight: 900, cursor: "pointer" },
  status: { color: "#67e8f9", fontWeight: 700 },
  feed: { display: "grid", gap: 14, marginTop: 18 },
  empty: { border: "1px dashed #475569", borderRadius: 16, padding: 18, color: "#cbd5e1", textAlign: "center" },
  record: { border: "1px solid #334155", borderRadius: 16, padding: 16, background: "#020617" },
  approvalCard: { border: "1px solid #f59e0b", borderRadius: 16, padding: 16, background: "rgba(69,26,3,.2)" },
  recordHead: { display: "flex", justifyContent: "space-between", gap: 12 },
  badge: { background: "#0c4a6e", color: "#a5f3fc", borderRadius: 999, padding: "8px 12px", fontSize: 12, fontWeight: 900, height: 32 },
  approvalBadge: { border: "1px solid #f59e0b", color: "#fcd34d", borderRadius: 999, padding: "8px 12px", fontSize: 11, fontWeight: 900, height: 32 },
  blocked: { marginTop: 10, color: "#fca5a5", borderTop: "1px solid #334155", paddingTop: 10 },
  reviewEvidence: { marginTop: 10, color: "#86efac", borderTop: "1px solid #334155", paddingTop: 10 },
  reviewActions: { display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8, marginTop: 14 },
  approveButton: { border: 0, borderRadius: 10, padding: 10, background: "#22c55e", color: "#052e16", fontWeight: 900, cursor: "pointer" },
  rejectButton: { border: 0, borderRadius: 10, padding: 10, background: "#f87171", color: "#450a0a", fontWeight: 900, cursor: "pointer" },
  escalateButton: { border: 0, borderRadius: 10, padding: 10, background: "#f59e0b", color: "#451a03", fontWeight: 900, cursor: "pointer" },
  footer: { marginTop: 18, border: "1px solid #334155", borderRadius: 14, padding: 14, textAlign: "center", color: "#cbd5e1", background: "rgba(15,23,42,.75)" },
};
