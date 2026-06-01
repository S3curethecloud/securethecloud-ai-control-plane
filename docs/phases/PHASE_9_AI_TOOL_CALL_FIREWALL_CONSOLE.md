# Phase 9 — AI Tool-Call Firewall Console

Status: Implementation Complete

## Goal

Add an interactive AI Tool-Call Firewall Console that previews requested AI tool calls before execution and explains whether each tool is allowed, blocked, requires approval, or requires redaction.

## Implemented

- Backend tool-firewall preview endpoint
- Per-tool firewall decision model
- Frontend AI Tool-Call Firewall Console
- Status outcomes:
  - allowed
  - blocked
  - requires_approval
  - redacted
- Tool-specific policy reasons
- Requested tool-call selector integration
- Evidence replay preservation
- Approval workflow preservation

## Tool Calls Covered

- search_documents
- call_api
- access_records
- write_files
- trigger_workflow
- send_message

## Boundary

This is a lab workflow demonstration. It does not provide real enterprise authorization, real regulated-system access, production enforcement, SOC 2 certification, identity-provider integration, or replacement of IAM/PAM/DLP/SIEM controls.
