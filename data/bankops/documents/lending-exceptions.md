---
document_id: BANKOPS-LENDING-EXCEPTIONS-001
version: 1.0
effective_date: 2026-01-01
owner: Lending Operations
status: active
synthetic: true
---

# Lending Exception Handling Standard

> Portfolio disclaimer: This fictional standard uses synthetic data and must not be used to make a real credit decision.

## Exception triggers

A lending application enters manual exception review when declared income cannot be verified, required affordability fields are incomplete, or a high-risk customer requests an amount above the configured review threshold.

## Required review

The reviewer must record the exception reason, source evidence, assessment, and final recommendation. A reviewer cannot approve an exception they originally created. High-risk exceptions require a second approver from Lending Risk.

## Decision boundaries

The copilot may summarize submitted evidence and locate this policy. It must never invent an approval, change an application status, or treat a model-generated recommendation as a lending decision.

## Escalation

An unresolved exception that remains pending for more than two business days must be escalated to the Lending Operations queue owner.
