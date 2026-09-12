# Funnel analysis: findings and recommendations

**Simulated data, not evidence about a real business.** Seed 42; 12,000 sessions; January–March 2026.

## Results
- 1,145 ordered purchases / 12,000 visits = **9.54% session conversion**.
- Largest proportional loss: **add_to_cart**, with 67.32% of eligible sessions dropping off (5,817 sessions).
- Mobile conversion: 7.83%; desktop: 12.3%. These differences are intentionally built into the generator.
- Removed 200 duplicate records and 1 orphan record. Out-of-order purchases remain in cleaned data but do not qualify for the ordered funnel.

## Three recommendations to investigate
1. Examine product-to-cart friction using product detail interactions, availability, and price/shipping visibility. Test a clearer product page. Primary metric: carted sessions / product-view sessions; guardrails: purchase conversion and return rate.
2. Inspect mobile checkout validation, payment errors, and load times. Test checkout simplification. Primary metric: ordered purchases / checkouts; guardrails: payment errors, order value, and refunds.
3. Review traffic intent and landing-page match by channel. Test channel-specific landing pages before changing spend. Channel rates alone cannot establish acquisition efficiency without spend, margin, and attribution data.

## Experiment design
Randomize eligible users before treatment and keep assignment stable across sessions. Predefine the hypothesis, primary metric, minimum detectable effect, power, and stopping rule. Estimate sample size from real baseline data; run through complete weekly cycles. Report intention-to-treat results with user-level uncertainty. Do not claim any recommendation has already caused a lift.

## Method and limitations
Unit = session, not unique user. A qualifying path requires strictly increasing timestamps in the same session: visit → view_product → add_to_cart → checkout → purchase. Repeated stage events count once using the earliest eligible event. Cross-session conversions and alternative paths are excluded. Equal timestamps do not satisfy ordering. Cohort month is session start, using UTC. The simulation includes complete sessions, so the final date is not right-censored.

Dashboard confidence intervals use the Wilson 95% binomial interval. They assume independent sessions; repeated users can violate this assumption, so treat these intervals as educational, not decision-grade. Use user-cluster bootstrap on real repeated-user data. Device/channel mixes may confound differences; segmentation is descriptive, not causal. Revenue is synthetic currency-neutral transaction value and is not used as a business KPI.

## Validation
PASS: unique cleaned IDs; one row per session; all ordered SQL paths match independent Python traversal; SQLite integrity.
