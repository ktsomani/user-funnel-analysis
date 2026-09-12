# E-commerce User Funnel Analysis

A complete, reproducible personal portfolio project using **Python + SQL + an interactive dashboard**. All data is synthetic. No API keys, paid services, or third-party Python packages are required.

## Start here
1. Open `dist/index.html` in your browser to explore the dashboard immediately.
2. Read `results/findings.md` for conclusions, recommendations, and limitations.
3. To rebuild everything, install Python 3.10+ and run `python build_project.py` from this folder.
4. Open `data/funnel.sqlite` with any SQLite client to explore the tables. Run `sql/funnel.sql` before `sql/segments.sql`.

The dashboard works offline. Device, traffic-source, and month filters recalculate the main funnel. Comparison panels deliberately retain all devices or months as labeled. Download CSV exports the active funnel with its filters.

## Business question
Where do visitors drop out of the purchase journey, and which segments deserve investigation?

## Project structure
| File | Purpose |
|---|---|
| `build_project.py` | Generate, validate, clean, analyze, and export data |
| `sql/funnel.sql` | Ordered five-stage session funnel |
| `sql/segments.sql` | Device, source, and monthly comparisons |
| `dashboard.html` | Dashboard source template; rebuild after editing |
| `dist/index.html` | Ready-to-open dashboard with embedded aggregates |
| `data/sessions.csv` | 12,000 synthetic sessions |
| `data/events_raw.csv` | Generated events including tracking noise |
| `data/events_clean.csv` | Deduplicated events with valid session links |
| `data/events_rejected.csv` | Audit trail with rejection reasons |
| `data/funnel.sqlite` | Queryable SQLite database |
| `results/` | CSV outputs, JSON summary, findings, and validation evidence |

## Data dictionary
**sessions:** `session_id` (unique session key), `user_id` (synthetic user; may repeat), `started_at` (ISO-8601 UTC), `device` (Mobile/Desktop/Tablet), `channel` (Organic/Paid Search/Social/Email).

**events:** `event_id` (deduplication key), `session_id` (session foreign key), `event_name` (visit/view_product/add_to_cart/checkout/purchase), `event_time` (ISO-8601 UTC), `revenue` (synthetic currency-neutral purchase value; zero otherwise).

**session_funnel:** session dimensions plus the earliest eligible timestamp for each stage. Null means that stage did not qualify.

## Metric contract
- Analysis unit: **session**, not user. Count each session at most once per stage.
- Path: Visit → View product → Add to cart → Checkout → Purchase.
- Every timestamp must be strictly later than the prior stage, within the same session.
- Overall conversion = ordered purchases / eligible visits.
- Step conversion = sessions at current stage / sessions at prior stage.
- Step drop-off = prior-stage sessions minus current-stage sessions.
- Cohort date = session start, UTC. Events belong to preassigned sessions; this project does not infer sessions from inactivity windows.
- Early purchases remain in clean event data but are excluded from qualified paths. This separates record quality from funnel semantics.

## Learning path
1. Inspect the raw CSV and explain why counting purchase events directly gives a different answer.
2. Trace the SQL CTEs for a complete, incomplete, and out-of-order session.
3. Reproduce device conversion with `segments.sql` and compare it with the dashboard.
4. Explain the largest proportional loss versus the largest absolute loss.
5. Present recommendations as hypotheses, with metrics and guardrails for validation.

## Validation and reproducibility
The fixed seed is 42. The pipeline checks unique cleaned IDs, SQLite integrity, one output row per session, and every session's SQL stage timestamps against an independent Python event traversal. Rebuilding regenerates the sample files and outputs; save any manual changes separately first. The generator intentionally introduces mobile checkout and source differences; these are educational inputs, not discovered facts about a real company.

## Adapting to real data
Replace `generate()` with a CSV loader that returns the same session/event fields. Agree on identity, attribution, timestamp timezone, session boundaries, conversion windows, cancellations, and refunds first. Preserve raw files; validate and quarantine malformed records; define how tied timestamps should be ordered. Check tracking completeness and exclude immature cohorts. Estimate uncertainty at user level when users have repeated sessions. Do not publish personal information in the dashboard.

## Portfolio description
“Built a reproducible e-commerce funnel analysis project using Python, SQLite, and an interactive dashboard. Implemented ordered session-level conversion logic, event deduplication, segmented analysis, and independent reconciliation checks on 12,000 simulated sessions. Developed testable recommendations and documented measurement limitations.”

Do not claim this project increased a real store's conversion or revenue. Findings are generated in `results/findings.md` after each run.
