# Security and control review — 2026-11-04

Controls are installed in the Contabo review deployment. Source/unit/HTTP checks
and live unsigned-request rejection do not constitute a production security audit.
Signed-in account and media acceptance remains pending.

| Boundary | Implemented control | Remaining verification / limitation |
| --- | --- | --- |
| User identity | Existing Open WebUI verified-user dependency, role checks, owned jobs/events; pending rejected | Real JWT/cookie/API-key and family account isolation require live app test |
| Control writes | Same-origin cookie writes, explicit origin denial,64KiB bodies | Native routes retain their existing controls; no new cross-origin deployment |
| Provider keys | Reuse existing tool valves or exact approved RunPod connections in-process; no credentials in ledger/browser | Existing Contabo key/configuration preserved; do not copy credentials into new plugin valves |
| Job/data access | Owned ledger rows and asset references; saved-chat owner check before media submission | Native uploads, signed URL expiration, iframe/cookie file permissions require real acceptance |
| Admin recovery | Metadata-only uncertain-job list and audited reconciliation; other users' outputs remain owner-only | Admin must review actual provider Requests before releasing uncertain work |
| Tool-result injection | Treat results as data; strict FAST/PRO labels; reasoning specialist receives no tools; endpoint catalog fixed | Prompt instructions cannot guarantee semantic resistance; quality/injection red-team acceptance still needed |
| Recursive/billed work | One reasoning per turn, video duration/count, atomic global concurrency, persistent deduplication and no automatic POST retry | Other native tools/direct models are outside this governor; model quality remains variable |
| Media/files | Approved HTTPS object-storage suffixes, no redirect following, size bound64MiB default, JPEG/MP4 signature checks, saved authenticated file URLs | Signature checks are not malware scanning; no DNS pinning or full media decoder validation; only trusted provider outputs intended |
| Input/output exhaustion | Bounded specialist/media prompts, speech JSON/text/WAV duration, max tokens, control bodies, event131KiB/result2MB limits | Native multipart ingress and overall disk quotas remain outside these adapters; monitor VPS disk |
| Spending | SQLite BEGIN IMMEDIATE reservations across processes, per-day/month/capability quotas, warnings and estimates | No provider/account hard cap; CPU, disk, native speech, direct models/API use bypass; prices can change; interrupted GPU may exceed estimates |
| Failure recovery | Persist IDs/results/events, cursor replay, cancel confirmation, unknown holds, explicit refresh/reconcile/retry | App crash cannot guarantee provider cancellation; provider output retention finite; saving after GPU completion can fail |
| Privacy/storage | Ledger on existing persistent mount,0600 database,0700 created directory; no raw input payload/key stored | Outputs/events and private source URLs can contain sensitive content; protect full data volume/backups, no end-to-end encryption added |

## Budget enforcement semantics

Defaults are household $2/day and$20/month, Helsinki calendar, two concurrent
operations, max5sec video and one video per turn. Counts: daily Fast100,
reasoning20, vision20, image10, quality3, video2, voice10; monthly video10 and
reasoning100. Defaults need owner review; admin can update policy; omitted fields preserve existing limits.
Zero capability count disables that capability. Global limits intentionally
prevent one family member from exhausting concurrent GPU budget.

Compute reserve is worst currently allowed pool hourly price × (request timeout
+ configured idle tail). Qwen/Gemma use$1.75/h, Fast/voice$0.75/h. Reservation
per request may substantially overcount a shared warm worker; it is deliberately
conservative and is not an invoice. Actual media-reported cost is used when valid;
compute stays estimated without invoice correlation. Failed/cancelled operations
can still be billed, so retain estimated cost. Definite provider rejection refunds
its reservation. Provider billing snapshots are admin-imported, USD-labeled,
separate from the ledger, and never silently reduce reservations or enforce a cap.

Unknown jobs hold reservations and concurrency indefinitely until the owner or
admin reviews provider state. This sacrifices availability to avoid duplicate
bills. `refresh` of a known provider ID reads status only, stores recovered output
as untrusted data, and does not execute tools or resubmit. An admin can reconcile
another account's uncertain job using metadata without reading its outputs.
Exact same-turn retries replay completed results. Identical same-chat requests
with changed assistant IDs are also deduplicated for120s; an intentional repeat
may need changed input or waiting. A fresh ID is not a billing escape hatch.

Calendar periods use the job's admission time. A job crossing midnight/month end
remains charged to its original admission period; in-flight work is not moved to
a new period. Shared native plugins must use one SQLite path on the existing
volume. Multi-host deployments/network filesystems need separate locking and
load tests; SQLite WAL across multiple machines is not claimed supported.

## Operational requirements before production

Preserve the existing Contabo encryption key and establish a private backup;
retain pinned app version and check file permissions. Verify real account/asset ownership and test
native voice bypasses. Keep unknown-job reconciliation visible to the admin.
Review disk growth and take private backups; no automatic retention deletion
was introduced. Never commit the ledger, family chats, uploaded media or keys.
Provider billing API snapshots lag and cannot justify clearing unknown tasks.

Existing direct models and native speech were preserved, as requested. Therefore
these application controls cannot guarantee a maximum total RunPod bill. A
future hard spend guarantee needs provider-side enforceable limits plus governing
all submission paths, with owner approval before changing family access. Do not
claim the default$20/month covers app hosting or the whole account.

The current Wan profile accepts five-second clips. Setting the duration cap below
five seconds disables this profile; unsupported shorter durations are rejected
before generating a starting image or submitting paid work.

Identical active/uncertain jobs remain protected against changed-message-ID
resubmission beyond the120s completed-result replay window, until reconciled.
