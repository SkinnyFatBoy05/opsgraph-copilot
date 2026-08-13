# Data provenance and safe use

OpsGraph is a portfolio and learning project. Every customer, case, SLA, employee, roster, payroll, and audit record in the repository is synthetic. Do not upload real customer, employee, payroll, financial, personal, confidential, or regulated data.

## BankOps

BankOps policies and operational records are fictional. The seed generator creates a small deterministic dataset so tests and demonstrations are repeatable. It is not based on a bank's production data, policies, customers, or internal procedures.

## AwardLens AU

The included payroll rows are synthetic. The narrow Retail Employee Level 1 rule parameters are a machine-readable educational summary of public facts from:

- [General Retail Industry Award 2020 (MA000004)](https://awards.fairwork.gov.au/MA000004.html), Fair Work Commission.
- [General Retail Industry Award pay guide](https://calculate.fairwork.gov.au/Download/AwardSummary?awardCode=ma000004&fileType=pdf), Fair Work Ombudsman, effective 1 July 2026.

The source manifest records the URLs, effective date, review status, and SHA-256 hash of the local rule file. The hash detects an unexpected local change; it does not prove that a rule remains current or legally complete. AwardLens deliberately excludes coverage decisions, juniors, apprentices, trainees, overtime, shiftworkers, allowances, overnight boundary cases, enterprise agreements, and other conditions that need qualified review.

Verify the current official award and pay guide before changing any rule. Outputs are educational comparisons, not legal, payroll, financial, or compliance advice. The MIT License covers this project's original code and documentation; third-party names and source materials remain the property of their respective owners.
