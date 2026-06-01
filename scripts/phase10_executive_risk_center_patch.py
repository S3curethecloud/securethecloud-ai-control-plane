from pathlib import Path

p = Path("frontend/app/page.tsx")
s = p.read_text()

# Add executive analytics derived state.
marker = '''  const pendingApprovals = useMemo(
    () => requests.filter((r) => r.policy_result.decision === "require_approval"),
    [requests]
  );'''

insert = '''  const pendingApprovals = useMemo(
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
  }, [requests, firewall, pendingApprovals.length]);'''

if marker not in s:
    raise SystemExit("Could not find pendingApprovals marker.")

s = s.replace(marker, insert)


# Insert Executive Risk Center after metrics section.
marker = '''        <section style={styles.workspaceFour}>'''

insert = '''        <section style={styles.executiveCenter}>
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

        <section style={styles.workspaceFour}>'''

if marker not in s:
    raise SystemExit("Could not find workspaceFour marker.")

s = s.replace(marker, insert)


# Add helper components before Metric.
marker = '''function Metric({ label, value }: { label: string; value: number }) {'''

insert = '''function RiskBar({ label, value, max, tone }: { label: string; value: number; max: number; tone: string }) {
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

function Metric({ label, value }: { label: string; value: number }) {'''

if marker not in s:
    raise SystemExit("Could not find Metric marker.")

s = s.replace(marker, insert)


# Add styles.
marker = '''  metrics: { display: "grid", gridTemplateColumns: "repeat(6,1fr)", gap: 14, marginTop: 18 },
  metric:'''

insert = '''  metrics: { display: "grid", gridTemplateColumns: "repeat(6,1fr)", gap: 14, marginTop: 18 },
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
  metric:'''

if marker not in s:
    raise SystemExit("Could not find metrics style marker.")

s = s.replace(marker, insert)

p.write_text(s)
print("Phase 10 Executive Risk Center patch applied successfully.")
