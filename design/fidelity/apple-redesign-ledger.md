# OpsGraph Apple redesign fidelity ledger

**QA date:** 2026-09-08

**Accepted references:**

- `design/concepts/apple-bankops-desktop.png`
- `design/concepts/apple-awardlens-desktop.png`
- `design/concepts/apple-bankops-mobile.png`

**Final renders:**

- `design/screenshots/bankops-live.png` at 1440 × 1080
- `design/screenshots/awardlens-live.png` at 1440 × 1080
- `design/screenshots/evaluations-live.png` at 1440 × 1080
- `design/screenshots/bankops-mobile.png` at 430 × 932

| Comparison point | Concept evidence | Render evidence | Resolution |
| --- | --- | --- | --- |
| Shell geometry | Desktop concepts use an inset floating sidebar, open white workspace, 24 to 28px outer radii, and narrow cool gutters. | Final desktop renders use a 224px sidebar, 16px gutter and inset, 24px sidebar radius, and 28px workspace radius. | Matched in CSS tokens and grid geometry. |
| Material restraint | The concepts place translucent material on navigation, controls, and evidence chrome while tables and excerpts remain opaque. | Final renders keep the sidebar, selected nav, composer, detail bar, and inspector chrome translucent. Tables, answer copy, SQL, and excerpts use solid surfaces. | Matched; blanket glass was intentionally avoided. |
| Typography | Concepts use a large, bold, left-aligned system display face and compact operational text. | BankOps renders at up to 42px, AwardLens and Evaluations at up to 50px, with a system-first stack and Inter fallback. Body content remains 13.5 to 14px desktop. | Matched with code-native system typography. |
| Query composer | Both desktop and mobile concepts use a rounded white input and prominent blue action, circular on mobile. | Final composer uses an 18 to 19px material surface, blue gradient action, and a 58px circular mobile control. | Matched; existing accessible action name remains `Run analysis`. |
| Result table | The concepts preserve a real dense table with restrained header fill and fine row dividers. | Final BankOps and AwardLens renders keep semantic tables, minimal cool dividers, tabular numerals, hover feedback, and horizontal mobile scrolling. | Matched without converting data into cards. |
| Evidence inspector | Desktop concept uses a glass outer rail with ranked E1, E2, E3 sources and opaque readable excerpts. | Final render shows the same ranking, confidence values, selected-source teal edge, external links, and opaque excerpt blocks. | Matched; the live application displays additional real sources when space allows. |
| AwardLens report | Concept uses one open report, a four-value summary strip, compact Verified Official state, clean table, and integrated findings composer. | Final AwardLens render preserves the deterministic-audit eyebrow, all real values, open report surface, summary separators, status colors, limitations, and composer. | Matched; original product copy takes precedence over an image-generation wording error. |
| Mobile continuation | Mobile concept uses a compact brand header, one-column investigation, horizontal table, detail surface, inline evidence, and floating three-item bottom navigation. | Final 430px render keeps all three workspaces directly visible, uses a two-line heading, touch-sized composer, real scrolling table, and fixed glass navigation. | Matched; heading size is slightly smaller than the concept so the real copy fits without crowding. |
| Evaluations consistency | The accepted system calls for open report layouts, large tabular values, teal success, and clear provenance. | Final evaluation render uses one summary strip, thin metric tracks, a full-width release gate, and quiet provider/suite/time provenance. | Matched through the shared report language without inventing new data. |

## Signoff

The final interface preserves the accepted composition, palette, type hierarchy, material behavior, component geometry, and responsive interaction model. All visible deviations are tied to real application content or viewport fit. The result meets the visual quality bar for the portfolio release.
