# Cost accounting correction — 2026-11-04

The USD 11.019672 reported after acceptance testing was a conservative admission
estimate, not a verified deduction from the RunPod balance. Earlier assistant
messages describing USD 0.98 as remaining allowance did not make that distinction
clear enough. The approved test ceiling remains USD 12 cumulatively; this change
does not open a fresh allowance or reset the existing jobs.

## Why the estimate is high

Compute reservations use the full request timeout plus an idle tail, multiplied
by a conservative hourly rate. Completion without an explicit provider cost
retains the whole reservation. Short requests therefore overstate runtime, and
multiple requests on one warm worker count the same idle allowance repeatedly.
The larger-model reservation also covers the more expensive permitted GPU pool.
This protects admission but does not measure the invoice.

At 20:45 UTC, RunPod's published November 4 billing records totaled USD 1.845964:
USD 1.523519 serverless, USD 0.303 public media endpoints and USD 0.019444 storage.
The latest follow-up testing was absent from that feed (including the known
second USD 0.30 video). This is an incomplete account-wide observation, not the
final test cost or wallet balance. It has not been substituted for governed job
usage, because the periods, scope and reporting delay differ.

## Changes

- Add a nullable `provider_reported` amount to jobs. Only explicit job costs from
  provider responses populate it. Admin resolution amounts remain estimates.
- Preserve existing `charged`/`reserved` amounts, job outputs and admission
  behavior. Historical rows have no trustworthy provenance marker and stay
  unconfirmed; migration never infers provider spend from an old number.
- Expose budget held, provider-reported subtotal/count, unconfirmed job count,
  unreconciled estimates and active reservations separately. Existing API fields
  remain compatible. Unknown amounts are not shown as zero-cost jobs.
- Show these distinctions in preview Activity. Partial provider job costs are
  explicitly distinct from the account bill. Normal limits remain USD 2/day and
  USD 20/month; this controls governed operations, not the entire RunPod account.
- Change only idle timeouts on existing endpoints: Gemma/Qwen 600s → 120s,
  voice 300s → 60s, Fast remains 60s. All retain min0/max1. No image, environment,
  GPU pool, model or public default changes. Source reservation tails match.

Shorter tails reduce idle waste but may increase cold starts and their cost.
Cold starts, execution and idle worker time are billed. At the current A40
serverless rate of USD 1.22/hour, one idle tail falls from about USD 0.203 to
USD 0.041, excluding startup, execution and storage. A new inference request
was deliberately not used to test natural shutdown.

## Verification and remaining work

Local: 105 Python tests and nine JS tests pass, including concurrent legacy
migration, preserved budget coverage after partial billing import, provider
versus admin cost provenance, and unknown/partial-cost display. JS syntax and
source bundle build are checked. The same 105 Python tests passed in the existing
Linux app container before install. After restart, the real authenticated usage
API returned 200 and unsigned access returned 401. All four installed plugin
sources exactly match the reviewed bundle. Before/after hashes confirm all 55
job records (including outputs) and policy are unchanged: USD 11.019672 held,
zero active reservation, USD 2/day and USD 20/month limits. All historical job
costs remain explicitly unconfirmed. Provider readback confirms only idle
timeouts changed, with min0/max1 retained. No paid request was submitted.

Remaining: reconcile completed worker sessions with delayed provider billing
without counting shared idle time twice. Until that exists, unconfirmed compute
estimates continue to count against admission and can block preview use. Do not
release them or report them as a wallet deduction. Fast's earlier manual recycle
does not establish reliable natural shutdown. Finnish/Swedish Fast quality and
real phone audio remain separate acceptance gaps; no model changed here.

Sources: [RunPod billing lifecycle](https://www.runpod.io/blog/failed-requests-real-charges-how-runpod-serverless-billing-works-when-workers-fail),
[current serverless rates](https://www.runpod.io/pricing).
