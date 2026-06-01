# Phase 12 — Managed Persistence & Demo Hardening

Status: Implementation Complete

## Goal

Harden the public AI Control Plane lab for recruiter/client demos by adding managed persistence readiness, demo reset, tighter CORS, and a repeatable interview demo script.

## Implemented

- SQLAlchemy persistence layer
- SQLite fallback for local development
- Fly Postgres support through DATABASE_URL
- Demo seed records persisted in storage
- Token-protected demo reset endpoint
- CORS origin allowlist
- Backend health endpoint reports persistence mode
- Recruiter/client demo script added to README

## Public URLs

- Frontend: https://securethecloud-ai-control-plane.fly.dev
- Backend health: https://securethecloud-ai-control-plane-api.fly.dev/health

## Verified

- Backend health reports persistence: postgres
- Dashboard reads persisted seeded demo data
- Demo reset endpoint protected by X-Demo-Reset-Token
- Demo reset returned four seeded governance records
- Dashboard returned seeded baseline after reset:
  - total_requests: 4
  - denied_requests: 1
  - high_risk_requests: 3
  - approval_required: 1
  - redacted_requests: 1
  - sensitive_data_attempts: 4
  - policy_violations: 1
  - human_approvals: 1

## Boundary

This is a public lab demo deployment. It does not provide enterprise IAM, production authorization, real regulated-system access, real customer data processing, SOC 2 certification, production audit assurance, or production enforcement authority.
