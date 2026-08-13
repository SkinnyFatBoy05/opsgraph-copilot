---
document_id: BANKOPS-ONBOARDING-001
version: 1.0
effective_date: 2026-01-01
owner: KYC Operations
status: active
synthetic: true
---

# Customer Onboarding Standard

> Portfolio disclaimer: This is fictional policy content created solely for the OpsGraph Copilot demonstration. It is not legal, compliance, or banking advice.

## Identity checks

Before activating a new customer, KYC Operations must record the customer's legal name, date of birth or business registration date, residential or registered address, and one government-issued identifier. The identifier must be verified against an approved synthetic verification source.

## Risk classification

Every customer receives either a `standard` or `high` risk rating. A high-risk customer requires a documented enhanced-review note and approval by a second analyst before an account may be activated. Standard-risk customers may be approved by one analyst when all required fields are complete.

## Incomplete applications

If required evidence is missing, the application must remain pending. The analyst must create a follow-up task and state which evidence is missing. The system must not silently replace a missing value with an inferred value.

## Evidence retention

The onboarding case must contain the verification outcome, analyst identity, decision time, and the version of this standard used for the decision.
