# Phase 11 — Fly.io Public Demo Deployment

Status: Implementation Complete

## Goal

Deploy the SecureTheCloud AI Control Plane lab to public Fly.io URLs for recruiter/client demo access.

## Deployment Model

- Frontend Fly app: securethecloud-ai-control-plane
- Backend Fly app: securethecloud-ai-control-plane-api
- Frontend public URL: https://securethecloud-ai-control-plane.fly.dev
- Backend health URL: https://securethecloud-ai-control-plane-api.fly.dev/health

## Implemented

- Backend Fly deployment
- Frontend Fly deployment
- Public backend health endpoint
- Public recruiter/client demo URL
- Frontend public API routing to Fly backend
- Phase 11 evidence committed and pushed

## Boundary

This is a public lab demo deployment. It does not provide enterprise IAM, managed persistence, production authorization, regulated-system access, SOC 2 certification, real customer data processing, or production enforcement authority.
