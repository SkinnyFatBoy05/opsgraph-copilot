# OpsGraph Apple-Inspired Interface Redesign

**Date:** 2026-09-08

**Status:** Approved for implementation by the user on 2026-09-08.

## Goal

Make OpsGraph feel like a polished, current product while preserving its strongest hiring signal: clear evidence, explicit guardrails, deterministic evaluation, and real operational workflows. The interface should help a recruiter or engineering leader understand the product within seconds and reward closer inspection with legible data and implementation depth.

## Accepted visual references

- `design/concepts/apple-bankops-desktop.png` defines the desktop shell, BankOps composition, palette, typography, controls, result table, detail bar, and evidence inspector.
- `design/concepts/apple-awardlens-desktop.png` defines the AwardLens report composition, metrics strip, table, verified status, and findings composer.
- `design/concepts/apple-bankops-mobile.png` defines the responsive composition, touch controls, horizontally scrollable data, inline evidence, and floating bottom navigation.

## Design system

The visual language follows Apple's current spatial principles without copying macOS window chrome or Apple branding. Translucent material is reserved for navigation, action controls, and inspector chrome. Answers, tables, SQL, policy excerpts, audit results, and evaluation data remain opaque and crisp.

- Canvas: true white and pale cool gray, with one restrained atmospheric blue field near the shell's upper left.
- Ink: very dark navy for headings, deep blue-gray for body text, cool gray for secondary text.
- Accents: Apple-like blue for primary action and selection, teal for verified/completed states, amber only for manual review, red only for errors or blocked release gates.
- Typography: system-first stack with Inter fallback; bold left-aligned display headings, readable 15 to 16px content, compact 11 to 13px control text, and tabular numerals for operational values.
- Geometry: concentric radii based on 12, 18, 24, and 28px; rounded 1.75px icons; one-pixel translucent highlights; restrained layered shadows.
- Motion: 180 to 260ms transitions using a smooth spring-like easing; subtle hover lift and press compression; no decorative animation; honor `prefers-reduced-motion`.
- Focus: visible keyboard ring with sufficient contrast. Touch targets remain at least 44px.

## Desktop shell

The shell uses an inset floating sidebar approximately 224 to 232px wide and 16px from the viewport edge. The OpsGraph mark and all three workspaces remain permanently discoverable. The active workspace receives a softly highlighted glass selection with a blue edge. The synthetic-data notice remains visible at the bottom.

The main product canvas floats beside the sidebar. BankOps uses a three-region layout: central task surface, right evidence inspector, and the shared sidebar. AwardLens and Evaluations use a broad report surface within the same shell. The header is integrated into each workspace instead of occupying a separate global bar.

## BankOps

The first view keeps this visible-copy lock:

- OpsGraph
- Bank Operations
- AwardLens AU
- Evaluations
- Evidence-first investigation
- Bank Operations Copilot
- Ask across synthetic policy and operational data.
- Which open complaint cases are late and what policy applies?
- Run analysis
- Synthetic data · Educational prototype

After a run, the existing completed/manual-review/error state, answer, operational table, limitations, generated SQL, trace, cost, and source evidence stay unchanged in meaning. The question composer becomes a wide rounded control with a circular or compact blue run action. The result table remains a real table with minimal dividers. The detail tabs become a floating control bar. The evidence inspector uses translucent outer chrome with opaque excerpts and a clear selected source.

## AwardLens

AwardLens keeps the existing workflow and copy, including Load demo payroll, Open audit report, rule version, real summary values, audit table, limitations, and Ask about the findings. The audit surface becomes one open report rather than a nested card collection. The four summaries form one typographic strip. Verified Official remains informative and compact. Calculated and Manual review retain distinct semantic colors.

## Evaluations

Evaluations uses the same open report language. Cases passed, mean latency, and estimated cost form a single summary strip. Quality metrics use thin tracks with large values and generous spacing. The release gate reads as the final decision surface, with teal for pass and red for failures. Provider, suite version, and generation time remain visible as provenance.

## Responsive behavior

Below 768px the desktop sidebar becomes a floating bottom navigation with all three workspaces visible. A compact top brand bar remains. Workspace content follows a single reading column with safe-area padding and enough bottom clearance for navigation. BankOps evidence becomes an inline section selected through the existing Evidence tab. Wide tables scroll horizontally without being converted into cards. AwardLens actions stack without losing labels. Evaluation summaries and metrics become a single column.

## Functional and accessibility constraints

All current APIs, data, states, role names, labels, links, tables, and tests remain valid. No new production claims or real-customer-data capability will be added. The synthetic-only educational scope remains visible. The redesign must preserve keyboard navigation, focus visibility, screen-reader names, responsive access to evidence, loading states, error states, manual-review states, and reduced-motion behavior.

## Verification

Run frontend unit tests, production build, and Playwright desktop/mobile workflows. Capture BankOps, AwardLens, Evaluations, and mobile screenshots from the finished app. Compare the accepted concepts and final renders in one QA pass, recording at least five concrete fidelity checks. Replace repository showcase screenshots and record a short LinkedIn video from the verified app that visibly demonstrates an allowed complaint-policy query, generated read-only SQL, evidence, trace, AwardLens manual-review boundaries, and evaluation guardrails.
