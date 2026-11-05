# RunPod account tracker

The administrator's `/preview/` header shows the available RunPod balance.
Press it to open Activity with the balance, reported spending today and this
month (UTC), observation timestamps and the provider-reported hourly rate.
Refreshes run once per minute while the page is visible, independently of chat
and media polling. RunPod billing can lag; these are account-wide figures,
including storage and use outside Family AI. Existing job estimates and budget
controls remain separate.

`GET /api/v1/family/account` requires the existing verified administrator session.
Ordinary members receive 403 and unsigned requests receive 401. Successful
responses have `Cache-Control: private, no-store`. The existing RunPod credential
is reused only in server memory; no credential is sent to the preview. The
backend caches readings for 60 seconds and shares concurrent refreshes. Provider
failures retain the last good figure as stale; missing values never become zero.
Daily/monthly rollovers invalidate prior-period totals.

Provider sources: [GraphQL account API](https://graphql-spec.runpod.io/) fields
`myself.clientBalance` and `currentSpendPerHr`, and the
[billing API specification](https://api.runpod.io/v2/openapi.json) endpoint
`/v2/billing?bucketSize=day|month&lastN=1` with `metadata.totals.totalAmount`.
Provider calls are read-only and submit no inference jobs.

## Deployment and rollback

Use the existing plugin bundle build/install workflow in
`docs/contabo-integration.md`, restart only Open WebUI, then publish the three
preview source files. The 2026-11-05 deployment is staged on the existing VPS at
`/opt/family-ai/integration/20261105-account-tracker/`.
`web-before/` retains the previous three assets and `plugin-before/` retains the
previous reviewed plugin sources without credential valves. To roll back, install
that plugin bundle with the same installer, restart Open WebUI and copy the three
`web-before/` files back to `/opt/family-ai/web/build/`. Do not restore a database
or remove chats, files or ledger history.

## Verification

Local checks pass: 121 Python tests and 10 JavaScript tests, bundle build,
JavaScript syntax and diff checks. Coverage includes account permissions in both
regular and bundled native framework routes, cache reuse, partial outages,
invalid amounts, UTC period changes and preservation of admission policy/jobs.
Browser rendering and phone/device behavior remain unverified: the browser
inspection was stopped by its URL safety check before deployment.

Live VPS checks after deployment: Open WebUI healthy, administrator account API
200 with no-store caching, unsigned API 401, all three figures fresh, repeated
reads reuse the server cache, and installed plugin sources match the bundle.
Public HTTPS preview assets returned 200 and matched the source bytes exactly.
There are no ordinary member accounts on this installation; member 403 behavior
was tested locally in the real framework and bundled route tests.

The first live reading was USD 15.530942 available, USD 0.002917 reported today,
and USD 10.395398 this month; these are timestamped observations, not fixed
balances. All 78 historical jobs, zero reservations, retained estimates of
USD 16.648839, USD 2/day and USD 20/month limits, stored configuration and plugin
valves have identical before/after fingerprints. No inference jobs were submitted
and no additional GPU test cost was incurred. Existing storage charges continue.
