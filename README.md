# SecureTheCloud AI Control Plane

**Status:** Lab Platform / Phase 0 Baseline

A governed AI access, policy, and evidence platform for regulated enterprise workflows.

This lab demonstrates how AI can assist, summarize, and recommend while access to sensitive data, tool calls, regulated information, and workflow actions remain gated by identity, policy, approval, and evidence validation.

## Visible Platform Doctrine

AI may assist, summarize, and recommend.
AI may not access sensitive data, invoke tools, expose regulated information, or execute actions without identity, policy, approval, and evidence validation.

## Lab Boundary

This is a production-shaped lab, not an enterprise-grade authorization system. It is suitable for demos, portfolio review, architecture validation, and workflow governance education.

It does **not** claim SOC 2 certification, production enforcement authority, real identity-provider integration, clinical system integration, banking-core integration, or replacement of enterprise IAM/PAM/DLP/SIEM controls.

## Core Scenario

An employee asks an AI assistant to summarize sensitive customer, patient, or financial data. The platform checks identity, role, data classification, policy, business purpose, approval state, and evidence logging before returning an allow, deny, approval-required, or redact decision.

## Modules

- AI Access Request Portal
- Identity Context Engine
- Data Classification Layer
- Policy Decision Engine
- AI Tool-Call Firewall
- Human Approval Gate
- Evidence Replay
- Executive Governance Dashboard

## Stack

- Frontend: Next.js / React / TypeScript
- Backend: FastAPI / Python
- Database-ready: PostgreSQL scaffold with in-memory seed fallback
- Policy: OPA/Rego-style policy file plus Python evaluator for local lab execution
- DevOps: Docker Compose, GitHub Actions, Terraform scaffold

## Quick Start

```bash
cp .env.example .env

docker compose up --build
```

Frontend: http://localhost:3000
Backend API: http://localhost:8000
API docs: http://localhost:8000/docs

## Local Backend Only

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Local Frontend Only

```bash
cd frontend
npm install
npm run dev
```

## Phase Model

All lab work is tracked under `docs/phases/`.

- Phase 0: Repository and doctrine baseline
- Phase 1: Backend governance API
- Phase 2: Frontend platform shell
- Phase 3: Policy decision and tool-call firewall
- Phase 4: Evidence replay and audit dashboard
- Phase 5: Docker, CI, and deployment readiness

## API Demo Flow

1. Create an AI access request.
2. Backend classifies risk and applies policy.
3. Decision returns `allow`, `deny`, `require_approval`, or `redact`.
4. Evidence event is captured.
5. Dashboard and evidence replay read backend state.
