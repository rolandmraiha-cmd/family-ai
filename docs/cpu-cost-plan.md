# Reduce CPU hosting cost

Checked 2026-11-01. Advice/preparation only: no CPU server has been ordered,
stopped or migrated.

## Current measured setup

Runpod CPU pod `ix476koa61pd4o` costs $0.08/hour. At 720 hours that is
**$57.60 per 30-day month**, before storage/tax. It has 2 vCPU and 8GB RAM;
the API snapshot showed 20% RAM and 0% CPU utilization. This is one idle
snapshot, not a peak-load measurement.

The 10GB network volume `vevppjlc9a` is mounted at `/app/backend/data`.
Its contents include private chats, accounts, documents and saved settings.
The running image is tagged `main`; determine its exact installed version/digest
before migration and restore that same version first, avoiding a database upgrade
and host move in one operation.

## Preferred choices

1. **Reuse the earlier Contabo VPS if still active and there is sufficient headroom.**
   Previous project records described 4 vCPU/~8GB at €5.50/month. This is historical,
   not current host verification. Incremental server rent could be zero. Check
   actual RAM, disk, current services and CPU use first; do not replace roland-agent.
2. **A new 4–8GB x86 VPS.** Four GB is a starting estimate for light Open WebUI,
   eight GB gives room for embeddings, documents and a light browser workload.
   A desktop with many tabs needs its own measured capacity budget.
3. **Manual stop/start of the Runpod CPU pod.** A temporary saving if an offline
   website between sessions is acceptable. Stopped compute is not billed, but disk
   and network volume charges persist. Do not automate this until the owner chooses
   the availability tradeoff. It does not make Open WebUI a scale-to-zero service.

All language-model inference remains on GPUs. A small CPU host will not be asked
to run the main AI model. GPU latency stays dominated by GPU startup and inference,
although RAG ingestion and browser actions still depend on CPU capacity.

## Price examples, not orders

| Option | Server / IPv4 cost | Caveat |
| --- | --- | --- |
| Existing Contabo | Potentially €0 additional rent | Current status and spare capacity unverified |
| Contabo Cloud VPS 4 (4 vCPU/8GB/100GB SSD) | Official page shows €5.50 reference price and €4.40 introductory price for first 24 months | Confirm billing country, tax, term, renewal and total at checkout; no purchase selected |
| Hetzner CX23 (2 vCPU/4GB) | €5.49 + €0.50 IPv4 = €5.99/month before VAT | Public product page currently marks unavailable |
| Hetzner CX33 (4 vCPU/8GB) | €8.49 + €0.50 IPv4 = €8.99/month before VAT | Public product page currently marks unavailable |

Backup storage and a domain, if needed, are additional. Do not compare unlike
tax/currency totals as an exact savings percentage. The main opportunity is
replacing hourly GPU-provider CPU hosting with a small fixed-price VPS.

## Migration sequence

1. Establish authorized SSH access to the selected host and check free RAM/disk,
   running containers, existing reverse proxy and ports. Do not dump secrets.
2. Back up the Open WebUI data using a consistent export or a maintenance-window
   copy after stopping writes. Preserve its existing encryption/session key through
   a secret-to-secret transfer, not repository files or chat. The owner enters
   credentials if direct transfer is unavailable.
3. Restore to separate persistent storage on the new host, using the same app
   version and existing settings. Add HTTPS through the existing proxy where possible.
   Never expose an unauthenticated model API or desktop port to the internet.
4. Verify login, old chats, uploads, RAG, GPU connections, streaming, voice and media.
   Configure the router only after this baseline works, or verify it separately
   before migration. Avoid making both changes at once.
5. Point users to the new HTTPS URL. Keep the old data intact for rollback; ensure
   only the chosen live instance receives new writes.
6. Stop the old CPU pod after the owner accepts the restored app. Retain its volume
   until backup/restore and rollback checks are complete. Do not permanently delete
   any resource without the owner's instruction.

## Sources

- Runpod authenticated `get_pod` snapshot for `ix476koa61pd4o`, 2026-11-01.
- [Contabo current offer](https://contabo.com/en-us/vps/)
- [Hetzner published prices](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/)
- [Hetzner IPv4 price](https://docs.hetzner.com/cloud/servers/primary-ips/overview/)
- [Hetzner availability](https://www.hetzner.com/cloud/cost-optimized/)
