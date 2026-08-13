---
document_id: BANKOPS-COMPLAINT-SLA-001
version: 1.0
effective_date: 2026-01-01
owner: Customer Care
status: active
synthetic: true
---

# Complaint Service-Level Standard

> Portfolio disclaimer: This service-level standard is fictional and applies only to the synthetic OpsGraph dataset.

## Acknowledgement targets

A priority complaint must be acknowledged within four business hours of opening. A standard complaint must be acknowledged within one business day. Business hours are Monday to Friday, 09:00 to 17:00 in the case timezone; this demonstration does not model public holidays.

## Overdue classification

An open complaint is overdue when its due time is earlier than the evaluation time. A closed complaint is not counted as currently overdue, even if it was resolved after its original due time. Reports must display the evaluation time used.

## Escalation

An overdue priority complaint must be escalated to the Customer Care queue owner. The case note must include the reason, current owner, elapsed business hours, and next action.

## Safe use of generated answers

The copilot may identify and summarize synthetic cases. A human operator remains responsible for contacting a customer, changing ownership, or closing a case.
