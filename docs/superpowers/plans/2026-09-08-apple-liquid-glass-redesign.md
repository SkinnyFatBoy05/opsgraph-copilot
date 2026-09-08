# OpsGraph Apple-Inspired Interface Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the OpsGraph frontend around the approved Apple-inspired spatial interface and produce verified desktop/mobile showcase media.

**Architecture:** Preserve the React component boundaries, API calls, state, and accessible role names. Replace the global header/grid with an inset shell, extend existing workspace markup only where semantic wrappers are needed, and implement the visual system through shared CSS tokens and responsive layout rules.

**Tech Stack:** React 19, TypeScript 5.8, Vite 7, Lucide React, Vitest, Testing Library, Playwright, CSS.

**Spec:** `docs/superpowers/specs/2026-09-08-apple-liquid-glass-redesign-design.md`

## Global Constraints

- Use translucent material only for navigation, action controls, and inspector chrome.
- Keep data, evidence, SQL, answers, audit results, and evaluation metrics opaque and crisp.
- Keep all existing API contracts, data, labels, role names, tests, and synthetic-only scope statements valid.
- Use a system-first font stack with Inter fallback and the 12/18/24/28px radius family.
- Use blue for primary action and selection, teal for successful/verified state, amber for manual review, and red for errors or failed release gates.
- Preserve all three workspace controls on desktop and mobile.
- Keep tables as tables and horizontally scroll them on narrow screens.
- Honor reduced motion and maintain visible keyboard focus.

---

### Task 1: Rebuild the application shell and navigation

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/DomainSwitcher.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- Consumes: `WorkspaceName`, `DomainSwitcher({ active, onChange })`, and existing workspace components.
- Produces: `.app-shell`, `.app-brand`, `.navigation-shell`, `.workspace-shell`, `.domain-navigation`, and mobile bottom navigation layout hooks.

- [ ] **Step 1: Strengthen the shell discovery assertion**

Add this assertion to the existing application-shell test:

```tsx
expect(screen.getByRole("button", { name: /Evaluations/i })).toBeVisible();
```

- [ ] **Step 2: Run the focused test**

Run: `npm test -- --run src/App.test.tsx`

Expected: PASS because all workspace controls already exist before visual changes.

- [ ] **Step 3: Refactor shell markup without changing navigation behavior**

Move `Wordmark` into the navigation shell, keep the mobile brand visible, and preserve the existing `active` state and `onChange` behavior. Add presentational wrappers only; do not add routes or duplicate buttons.

- [ ] **Step 4: Implement shared tokens and shell CSS**

Define exact semantic tokens for canvas, material, ink, muted text, line, accent, success, warning, danger, radii, shadows, and motion. Implement the inset glass sidebar, floating active navigation item, open workspace canvas, compact mobile brand, bottom safe-area navigation, focus rings, hover/press feedback, and reduced-motion override.

- [ ] **Step 5: Verify and commit**

Run: `npm test -- --run src/App.test.tsx && npm run build`

Expected: shell test and TypeScript/Vite production build pass.

Commit: `feat: rebuild OpsGraph application shell`

### Task 2: Restyle the BankOps investigation surface

**Files:**
- Modify: `frontend/src/features/bankops/BankOpsWorkspace.tsx`
- Modify: `frontend/src/components/QuestionComposer.tsx`
- Modify: `frontend/src/components/AnswerPanel.tsx`
- Modify: `frontend/src/components/EvidencePanel.tsx`
- Modify: `frontend/src/components/SqlPanel.tsx`
- Modify: `frontend/src/components/TracePanel.tsx`
- Modify: `frontend/src/components/CostPanel.tsx`
- Modify: `frontend/src/components/IngestionPanel.tsx`
- Modify: `frontend/src/styles.css`
- Verify: `frontend/src/features/bankops/BankOpsWorkspace.test.tsx`
- Verify: `frontend/e2e/bankops.spec.ts`

**Interfaces:**
- Consumes: existing `ChatResponse`, `RuntimeConfig`, detail tabs, question handlers, and evidence selection.
- Produces: desktop central canvas plus evidence rail, mobile inline evidence, glass question/action controls, crisp result/detail surfaces, and unchanged accessibility names.

- [ ] **Step 1: Add minimal presentational hooks**

Add class names and semantic wrappers for the heading row, run result region, detail surface, evidence rail material, and compact action label. Keep the current request cancellation, loading, error, manual-review, selected-evidence, and tab behavior unchanged.

- [ ] **Step 2: Implement the accepted desktop composition**

Match `design/concepts/apple-bankops-desktop.png`: large heading, rounded composer, blue run action, open answer copy, minimally divided table, floating detail bar, opaque SQL surface, and translucent evidence inspector chrome.

- [ ] **Step 3: Implement the accepted mobile composition**

Match `design/concepts/apple-bankops-mobile.png`: single-column content, touch-sized composer, horizontal table scrolling, four accessible detail tabs, inline evidence when selected, and sufficient bottom clearance for navigation.

- [ ] **Step 4: Run focused unit and browser workflows**

Run: `npm test -- --run src/features/bankops/BankOpsWorkspace.test.tsx`

Run: `npm run test:e2e -- bankops.spec.ts`

Expected: completed, manual-review, network-error, evidence, SQL, trace, and mobile-accessibility assertions pass.

- [ ] **Step 5: Commit**

Commit: `feat: redesign BankOps investigation workspace`

### Task 3: Unify AwardLens and Evaluations

**Files:**
- Modify: `frontend/src/features/awardlens/AwardLensWorkspace.tsx`
- Modify: `frontend/src/features/evaluation/EvaluationView.tsx`
- Modify: `frontend/src/styles.css`
- Verify: `frontend/src/features/awardlens/AwardLensWorkspace.test.tsx`
- Verify: `frontend/src/features/evaluation/EvaluationView.test.tsx`
- Verify: `frontend/e2e/awardlens.spec.ts`

**Interfaces:**
- Consumes: existing AwardLens audit response, findings, question flow, evaluation report, quality metrics, and release-failure list.
- Produces: one open AwardLens report with metrics strip and integrated question control; one open evaluation report with summary strip, metric lanes, release gate, and provenance.

- [ ] **Step 1: Add presentational report wrappers**

Group real summary values inside shared strip containers and add a report-body hook. Preserve headings, button/link names, table semantics, and all current values.

- [ ] **Step 2: Match the AwardLens concept**

Implement `design/concepts/apple-awardlens-desktop.png` with a quiet toolbar, open audit surface, four-column summary strip, clean table, compact verified indicator, limitations, and integrated findings composer. Stack controls and summaries at mobile widths.

- [ ] **Step 3: Apply the report language to Evaluations**

Use large tabular summary values, thin quality tracks, a strong release-gate surface, and quiet provenance. Render failure state with the existing red semantics.

- [ ] **Step 4: Run focused verification**

Run: `npm test -- --run src/features/awardlens/AwardLensWorkspace.test.tsx src/features/evaluation/EvaluationView.test.tsx`

Run: `npm run test:e2e -- awardlens.spec.ts`

Expected: demo load, audit values, manual-review boundary, report link, grounded question, evaluation metrics, provenance, and release failures pass.

- [ ] **Step 5: Commit**

Commit: `feat: unify AwardLens and evaluation reports`

### Task 4: Visual QA, repository screenshots, and showcase video

**Files:**
- Modify: `design/screenshots/bankops-live.png`
- Modify: `design/screenshots/awardlens-live.png`
- Create: `design/screenshots/evaluations-live.png`
- Create: `design/fidelity/apple-redesign-ledger.md`
- Create: `C:/Users/kisho/OneDrive/Documents/job search/04_LinkedIn/OpsGraph_Showcase_2026-09-08/OpsGraph_LinkedIn_Showcase_Apple.mp4`

**Interfaces:**
- Consumes: the finished local app, approved concepts, Playwright workflows, and existing LinkedIn post copy.
- Produces: final screenshots, fidelity ledger, short H.264 showcase video, and verified release evidence.

- [ ] **Step 1: Run the full frontend quality gate**

Run: `npm test -- --run && npm run build && npm run test:e2e`

Expected: all unit tests, production build, desktop browser tests, and mobile browser tests pass.

- [ ] **Step 2: Capture native comparison screenshots**

Use the in-app browser first at desktop and mobile dimensions. Exercise BankOps, AwardLens, and Evaluations before capture. Use Playwright only if the browser cannot capture a reliable artifact.

- [ ] **Step 3: Complete the fidelity ledger**

Compare concept and render in the same QA pass using `view_image`. Record at least: shell geometry, type scale, color/material, composer/action, table density, evidence inspector, AwardLens summary strip, and mobile navigation. Fix visible drift before signing off.

- [ ] **Step 4: Record the replacement video**

Create a 20 to 25 second H.264 video at LinkedIn-friendly dimensions. Show the allowed complaint-policy question, completed response, operational table, generated read-only SQL, evidence, agent trace, AwardLens manual-review rows, and Evaluations release gate. Keep overlays short, use no em dash characters, and make the allowed lines readable.

- [ ] **Step 5: Verify and commit**

Inspect the video with a contact sheet and probe duration, dimensions, codec, and file size. Re-run changed-scope checks, confirm `git diff --check`, and commit screenshots plus fidelity evidence.

Commit: `docs: refresh OpsGraph product showcase`
