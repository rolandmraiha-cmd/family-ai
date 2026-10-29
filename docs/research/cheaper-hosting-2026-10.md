# Cheaper ways to run Family AI (research, 2026-10-29)

Prices marked * come from third-party price aggregators and blogs, not the providers' own pages. Check them before switching.

## What we pay now

| Item | Price | Per month |
|---|---|---|
| Open WebUI CPU pod (always on) | $0.08/h | **about $58** (the biggest fixed cost) |
| Network volume, 10 GB | $0.07/GB | $0.70 |
| LLM serverless (A40 48 GB) | $1.22/h while running | about $0.30 per chat session (cold start + use + 10 min idle) |
| Voice | $0.58–0.69/h while running | cents per use |

Actual serverless spend for the setup week, including all the tests: **$2.39** (billing API).

## Option A: move Open WebUI off RunPod (saves about $50/month)
- Open WebUI doesn't need a GPU. A small EU VPS (for example Hetzner, which has data centers in Finland and Germany) costs a few €/month* instead of about $58.
- It can keep calling the same RunPod endpoints.
- Work: move the data volume and set up HTTPS. About 1–2 hours.

## Option B: pay per token instead of per GPU-hour (the cheapest by far)
Hosted APIs run the same open models and charge only for the words processed. There's no cold start and no idle cost.

| Provider | Model | Price per 1M tokens (input / output) | Notes |
|---|---|---|---|
| OpenRouter / DeepInfra | Gemma 4 31B | about $0.10–0.14 / $0.34–0.40* | US providers. Not available through OpenRouter's EU in-region routing. |
| DeepInfra | Qwen3.8 27B | $0.15–0.20 / $1.88–2.50* | |
| Scaleway (France) | Gemma 4 26B A4B | about $0.25 / $0.50* | EU, zero data retention claimed*, 1M free tokens to start |
| Nebius (Finland region) | Gemma 4 31B | price not confirmed | EU |
| Google Gemini API | Gemma 4 31B | free (rate-limited)* | Free-tier prompts may be used by Google: not private |

**Example:** a family using about 500k tokens a day would pay roughly $2–5/month on Gemma 4 31B. On RunPod serverless the same use costs about $1 per day of active use.

**Trade-off:** chats go to a third-party company. They aren't on your "own" GPU. EU providers with no-retention terms (Scaleway, Nebius) are the most private of these options.

## Option C: other serverless GPU platforms

| Platform | 48 GB GPU per hour | Notes |
|---|---|---|
| RunPod (now) | A40 $1.22 (serverless) | Works; FlashBoot; EU data centers |
| Modal | L40S about $1.95* | **$30 of free credits every month*** covers about 15 GPU-hours, so light use could be free. US-centric. Moving over is a rewrite. |
| Vast.ai serverless | A40 about $0.40*, no serverless surcharge* | Cheapest per hour, but the GPUs belong to random marketplace hosts. Bad for private family data, and reliability varies. |
| Beam | L40S about $0.76* | Smaller provider |

## Free tweaks on the current setup
- Idle timeout 10 min → 5 min: about $0.10 cheaper per session. The trade-off is more cold starts between messages.
- Use only Family AI (Gemma) by default: that's already the case.

## Recommendation
1. **Option A**: biggest saving with no change for the family, and everything stays private.
2. If you're willing to send chats to an EU provider: **Option B with Scaleway or Nebius**. It costs a few dollars a month, with no waiting for start-up. Keep RunPod Qwen as an optional "private" model.
