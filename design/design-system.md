# OpsGraph Interface Design System

## Accepted concept references

- `design/concepts/bankops-desktop.png` — 1536 × 1024 primary BankOps completed-hybrid state.
- `design/concepts/awardlens-desktop.png` — 1536 × 1024 primary AwardLens completed-audit state.
- `design/concepts/bankops-mobile.png` — 862 × 1823 responsive BankOps state.

These Image Gen outputs are implementation references, not shipped UI assets. All product text, controls, tables, icons, states, and evidence remain code-native.

## Visual point of view

OpsGraph should feel like serious financial-operations software: evidence-first, calm, exact, and inspectable. The signature motif is a thin teal provenance connector between a claim or selected row and its cited source. The interface uses open rails and tables rather than a mosaic of decorative cards.

## Layout

### Desktop

- App header: 64px high with a 224px wordmark region.
- Navigation rail: 224px wide, fixed at the left edge.
- Main workspace: flexible width with a 48px outer gutter and 24px vertical rhythm.
- Evidence inspector: 340px wide, separated by a single border.
- Result details: open answer/table region followed by SQL and agent-trace tabs.
- Tables: full-width rows with 40–44px density and sticky headers where scrolling is required.

### Mobile

- Single column below a 64px top bar.
- Domain selection becomes a two-segment control.
- Composer and action stack vertically.
- Wide tables use a labelled horizontal scroller rather than collapsing into cards.
- Evidence, SQL, trace, and cost share one tabbed panel.
- The synthetic-data notice remains visible at the bottom of the workflow.

Breakpoints:

- `>= 1180px`: desktop rail + workspace + inspector.
- `768–1179px`: compact rail + workspace; inspector becomes an overlay drawer.
- `< 768px`: top navigation, single column, tabbed details.

## Color tokens

| Token | Value | Use |
|---|---|---|
| `--canvas` | `#FFFFFF` | Primary background; must remain true white. |
| `--canvas-subtle` | `#F6F8FB` | Quiet header, table header, and selected-row backgrounds. |
| `--ink` | `#0A1933` | Headings and primary text. |
| `--text` | `#26344D` | Body and control text. |
| `--muted` | `#667085` | Secondary metadata. |
| `--border` | `#D8E0EB` | One-pixel dividers and input outlines. |
| `--accent` | `#075FE4` | Primary action, selected navigation, active tabs. |
| `--accent-soft` | `#EEF4FF` | Selected navigation and row tint. |
| `--success` | `#07877D` | Completed and consistent statuses. |
| `--success-soft` | `#E7F7F4` | Success status background. |
| `--danger` | `#D92D20` | Discrepancy and unsafe states. |
| `--danger-soft` | `#FFF0EF` | Discrepancy background. |
| `--warning` | `#B76E00` | Manual-review state. |
| `--warning-soft` | `#FFF5E6` | Manual-review background. |

No gradients, glows, glass effects, tinted white page backgrounds, or decorative chart colors are allowed.

## Typography

- Family: `Inter`, bundled with the frontend, then `Segoe UI`, `Arial`, sans-serif.
- Workspace heading: 28px/34px, weight 700, tracking `-0.02em`.
- Section heading: 16px/22px, weight 650.
- Body: 14px/21px, weight 400.
- Controls and tabs: 13px/18px, weight 550.
- Table cells: 12.5px/18px; numeric cells use `font-variant-numeric: tabular-nums`.
- Metadata/captions: 12px/17px, weight 450.
- Mobile workspace heading: 25px/31px.

## Spacing, borders, and motion

- Spacing scale: 4, 8, 12, 16, 20, 24, 32, and 48px.
- Standard control height: 40px; primary composer action: 44px.
- Radius: 8px controls, 10px grouped panels, 999px only for compact status labels.
- Border: 1px `--border`; selected edge: 3px `--accent`.
- Shadows: overlays only, `0 16px 40px rgb(10 25 51 / 12%)`.
- Interaction transition: 160ms ease-out; disabled when `prefers-reduced-motion` is set.

## Components

- `AppShell`: header, navigation, workspace, inspector, and responsive drawer boundary.
- `Wordmark`: small node-ring mark plus “OpsGraph”; code-native SVG and text.
- `DomainNavigation`: Bank Operations, AwardLens AU, Evaluations.
- `QuestionComposer`: two-line question input, character count, submit action.
- `RunStatus`: icon, status text, elapsed time, and fallback/manual-review reason.
- `AnswerPanel`: prose, stable citation anchors, and result table.
- `EvidencePanel`: source count, source rows, excerpts, stable IDs, provenance connector.
- `SqlPanel`: read-only code display, dialect/limit metadata, copy control.
- `TracePanel`: ordered supervisor/specialist/verifier steps with duration and result.
- `CostPanel`: latency, tokens, model, prompt version, and estimated cost.
- `AuditActions`: load demo, local-only upload, run audit, download HTML report.
- `AuditSummary`: four open summary columns, not floating cards.
- `PayrollTable`: tabular currency, selected row, discrepancy/consistent/review/invalid states.
- `CalculationInspector`: immutable calculation lines, rule evidence, explanation, limitations.
- `EvaluationView`: release gates, route/retrieval/SQL metrics, report provenance.

## Icons

Use Lucide React icons only, with 18px default size, 1.75px stroke, round joins/caps, and `currentColor`. Required metaphors:

- `Landmark` — Bank Operations
- `FileCheck2` — AwardLens AU
- `ClipboardCheck` — Evaluations
- `Search` — composer
- `Play` — run
- `FileText` — policy evidence
- `Database` — SQL/data evidence
- `GitBranch` — agent trace
- `ShieldCheck` — verification and prototype notice
- `Calculator` — deterministic calculation
- `TriangleAlert` — discrepancy
- `CircleHelp` — manual review
- `Download` — report
- `Menu` — mobile navigation

## Allowed visible copy

Above the fold may contain only:

- `OpsGraph`
- `Bank Operations`
- `AwardLens AU`
- `Evaluations`
- `Bank Operations Copilot`
- `Ask across synthetic policy and operational data.`
- `AwardLens AU`
- `Audit synthetic payroll records with deterministic rules.`
- `Run analysis`
- `Load demo payroll`
- `Upload CSV`
- `Run audit`
- `Synthetic data · Educational prototype`
- `Synthetic data · Educational prototype · Not legal or payroll advice`

Question text, results, counts, dates, identifiers, currency values, model names, durations, tokens, and costs are real application data and may differ from the concept screenshots.

## Intentional concept exclusions

The generated images included Help, History, avatar, Settings, and Sign out controls that are not part of the approved product specification. They will not be implemented. Award values, dates, employee/customer labels, and result counts shown by Image Gen are illustrative; the implementation must render the deterministic synthetic fixtures and the verified 2026 rule manifest instead.

## Core interactions

1. Switch domains without losing the current domain's last result.
2. Submit a suggested or edited BankOps question and see loading, completed, fallback, manual-review, or failed status.
3. Move among evidence, SQL, trace, and cost while preserving the answer.
4. Select a cited claim or result row and highlight the corresponding evidence.
5. Load the AwardLens demo, run the audit, select a finding, inspect calculation/evidence/trace, and download the report.
6. Inspect evaluation results without triggering a paid or live evaluation.
7. On mobile, access every desktop detail through the tabbed lower panel.

## Image-generation provenance

The three references were generated with the built-in Image Gen tool from structured `ui-mockup` prompts. The prompts required an implementation-ready financial-operations dashboard, true-white/cool-gray canvas, open rail/table composition, code-native controls, evidence/SQL/trace visibility, and explicit avoidance of marketing layouts, gradients, glass effects, bento grids, stock art, and decorative metrics.
