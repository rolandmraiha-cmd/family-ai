# Best open-weight models for a private family AI (as of 2026-10-26)

Deep-research run: 22 sources fetched, 25 claims checked by 3 adversarial voters each (18 confirmed, 7 refuted).

## Bottom line
**Xiaomi MiMo-V2.6-Pro** is the strongest open-weight reasoning model right now.
- 1.02T total / 42B active parameters (MoE), 1M-token context, MIT license, weights on Hugging Face (released ~Sep 21-22, 2026).
- #1 open model on Artificial Analysis Intelligence Index v4.3.2 (~46) and on BenchLM (73.6, a score BenchLM marks "Estimated").
- Humanity's Last Exam: 49.4% (Kimi K3: 46.9%).

Open models still trail closed ones. On BenchLM's reasoning board, ranks 1-11 are all proprietary, led by Claude Opus 5.5 at 86.6 (~13 points above MiMo). Vision is the biggest gap: the best open model ranks #23 of 63 on Roboflow's benchmark.

## Ranking by ability

| Ability | Best open pick | Runners-up / notes |
|---|---|---|
| Reasoning (main brain) | MiMo-V2.6-Pro | DeepSeek V4.1 Flash 1017 (~45), GLM-5.3 (~45), Step 5 Preview (~44, 600B/27B), Kimi K3 (~44, deprecated, disputed license), Qwen3.8 Max (2.4T-A95B, text-only, custom license) |
| Agentic coding / tools | GLM-5.3 (753B/40B MoE, 1M context, 128K output, text-only) | DeepSeek V4.1 Flash. GLM-5.2 reported 62.1% on SWE-bench Pro (vendor figure) |
| Vision / documents | Qwen3.8 27B (Apache 2.0) | Qwen3.6 27B, Qwen3.6 35B-A3B |
| Speech-to-text | whisper.cpp | — |
| Text-to-speech | Kokoro-82M (runs on CPU or GPU, 8 languages) | — |
| Speech-to-speech | **Not verified.** Open models were far behind closed ones in older data | Use the STT → LLM → TTS pipeline instead |
| Image generation | **Not verified.** No claim survived checking | Needs a follow-up search (FLUX / Qwen-Image / HiDream, etc.) |

## Hardware (what a ~1T model costs to host)
Verified Kimi K2.6 figures (1T/32B MoE), which serve as a proxy:
- Full weights: ~610GB
- Unsloth GGUF: UD-Q2 ~340-350GB, UD-Q4_K_XL ~584GB, UD-Q8 ~595GB

MiMo-V2.6-Pro is an inferred estimate, not measured: roughly 1TB+ of GPU or unified memory at FP8, or ~350-600GB quantized. That means a multi-GPU server (e.g. 8× H200 / B200 class) or several large-memory Macs clustered together. The 27B vision model fits on a single 24-48GB GPU.

## How to build it
**Deploy + customize (recommended path)**
- Serve each model with **vLLM** (or SGLang). They all expose OpenAI-compatible `/v1` APIs.
- Use **Open WebUI** as the family front end: set `OPENAI_API_BASE_URL` to the vLLM `/v1` endpoint, or add connections in the admin settings.
- Point voice at **whisper.cpp** (STT, default `:2022/v1`) and **Kokoro-FastAPI** (TTS, default `:8880/v1`).
- This puts every model behind one UI. Add memory and document search (RAG) inside Open WebUI.

**Fine-tuning (optional)**
- **LoRA** forgets less general ability than full fine-tuning (0.617 vs 0.545 retention) but learns less (HumanEval 0.224 vs 0.263). It is the safe choice for persona, style and family-specific knowledge.
- **Distillation** from a stronger teacher can genuinely widen a smaller model's reasoning.
- Researchers disagree on whether RL actually teaches new reasoning. The "RL doesn't expand reasoning" claims were refuted in verification.
- Don't expect a home fine-tune to make MiMo itself reason better. Prompts, RAG and tools usually beat fine-tuning the flagship.

## Recommended family stack
1. **Brain:** MiMo-V2.6-Pro on vLLM/SGLang (multi-GPU server or cloud GPUs)
2. **Coding/agents:** GLM-5.3 (or DeepSeek V4.1 Flash)
3. **Eyes:** Qwen3.8 27B for photos, screenshots and documents
4. **Ears/voice:** whisper.cpp + Kokoro-82M
5. **Front end:** Open WebUI with accounts per family member, memory and RAG
6. **Customization:** system prompts + RAG first; LoRA adapters only for persona/style

## Caveats
- Nearly every model above was released July-October 2026, and rankings change monthly. Scores from different Artificial Analysis index versions aren't comparable.
- The rankings come from aggregators (Artificial Analysis, BenchLM, Roboflow) plus one blog. Some benchmarks are vendor-reported.
- Check each model's license. None blocks personal use.

## Not yet verified (open questions)
- Best open image-generation model and the VRAM it needs
- Real memory and serving support for MiMo-V2.6-Pro, GLM-5.3 and DeepSeek V4.1 at usable speed
- Best open speech-to-speech/omni model compared with the STT+TTS pipeline
- How much reasoning quality abliteration (uncensoring) costs on 2026 MoE models

## Key sources
- https://artificialanalysis.ai/models/open-source
- https://benchlm.ai/best/reasoning-models · https://benchlm.ai/best/open-source
- https://geotoolbox.ai/blog/best-open-source-llms
- https://playground.roboflow.com/models/task/vision-language
- https://unsloth.ai/docs/models/kimi-k2.6.md
- https://docs.vllm.ai/en/latest/deployment/frameworks/open-webui/
- https://voice-mode.readthedocs.io/en/stable/installation-tools/
- https://arxiv.org/html/2405.09673v2 (LoRA vs full fine-tuning) · https://arxiv.org/pdf/2504.13837v3 (RL and reasoning)

---

# Part 2: Voice, agent bots and hardware (2026-10-27)

> **Status:** The second research run collected these claims from their sources, but the cross-checking step failed (usage limit) and was not re-run. Treat everything below as **sourced but not cross-checked**. Image and video generation got no usable results, so they are still open.

## What Grok Bot and dots are
- **Grok Bot** (xAI, launched Aug 11 2026): an agent that runs on its own permanent cloud computer with a browser, files, a terminal, connectors and MCP. It operates screens like a person would. Early beta, included with SuperGrok Heavy / Cursor Ultra.
- **dots** (OpenAI, launched Sep 29 2026): always-on GPT-6 Astra agents, each with its own cloud computer and browser. More than 4,000 app plugins. Works in the background, but only reads from connected apps while doing so. Included with ChatGPT Pro (not in the EEA/UK/Switzerland).
- **What to copy:** one sandboxed VM per agent, plus connectors (MCP), memory, and a scheduler for background tasks.

## Building your own agent bots
| Piece | Option | Note |
|---|---|---|
| Brain for computer use | **MiMo-V2.6-Pro**: 82% on OSWorld-Verified (Flash: 80.8%) | Above GPT-5.5 (78.7%). The same model is also the reasoning pick |
| Small or fast computer-use model | **Holo3-35B-A3B** (H Company): 82.6% OSWorld-Verified, ~3B active parameters | Cheap to run all the time |
| Small all-rounder | **Qwen3.8-27B**: 84.3% OSWorld-Verified | Within ~1-2 pts of top Claude models; check that it's open-weight |
| Closed bar | Claude Fable 5.1: 86.0%; best agent framework: 90.2% | Open models are now close here |
| Agent framework | **Hermes Agent** or **OpenClaw**, plus **Cua Driver** (open source, MCP computer-use tool) | Cua can control a real desktop in the background or run inside a VM |
| Agent S3 framework | 72.6% OSWorld (with best-of-N) | Top scores rely on GPT-5 plus UI-TARS-1.5-7B for locating screen elements, so it isn't fully open |
| Sandbox per bot | A Docker container or VM per agent (e.g. a RunPod pod, or a local VM) | Copies the "own cloud computer" design |

## Voice
- **Pipeline is best for now:** a March 2026 paper found that no fully self-hosted real-time all-in-one voice model was practical. Qwen3-Omni's real-time speech output only worked through its cloud API. A pipeline (speech-to-text → LLM → text-to-speech) reached about 750 ms to the first spoken audio.
- **NVIDIA Nemotron VoiceChat** (Aug 2026): 11B, full-duplex (can listen and talk at once), can call tools mid-conversation, about 450-480 ms to take turns, and the best open score on Big Bench Audio (38.8%). Closed models score about 80-93%. English only, 2-minute memory, needs an 80GB GPU, weights marked for research use.
- **NVIDIA PersonaPlex** (7B, built on Moshi): full-duplex, very fast speaker switching (0.07s), clones a voice from a short sample, and takes a persona set by text. Good for a natural-feeling family voice.
- **Recommendation:** use the pipeline (whisper/Parakeet → MiMo or a fast model → Kokoro, or a voice-cloning text-to-speech model) for smart answers. Optionally add PersonaPlex for fast, casual back-and-forth chat.

## Hardware and cost (GLM-5.3 figures from vLLM's official recipe)
- GLM-5.3: about 743B total / 39B active parameters, native FP8. **Fits on one 8× H200 node** (141GB each). The full 1M context needs 8× B200. NVFP4 version: about 465GB, Blackwell GPUs only.
- MiMo-V2.6-Pro (about 1T parameters) will need at least as much: plan on 8× B200/B300 or a multi-node setup at FP8.
- **RunPod prices:** H200 $3.59-5.29/hr, B200 $5.98-7.99/hr, B300 $6.94-8.99/hr.
  - 8× H200 always on: **about $21k-31k per month**
  - On demand, for example 3 hours a day: about $2.6k-3.8k per month
- **Cheaper option:** run small models all the time (Qwen3.8-27B, Holo3-35B-A3B and voice all fit on 1-2 GPUs, or a home RTX/Mac). Start the big MiMo node only for hard tasks.

## Security rules for bots with account access
- Give each bot its own VM or sandbox, and its own accounts and tokens with the fewest permissions possible. Never use your main email or bank login.
- Background work is read-only by default, like dots. Sending, buying or deleting needs a human to approve it.
- Keep secrets in a vault, not in prompts, and rotate them.
- Treat web pages and emails the bot reads as untrusted, because they can contain hidden instructions (prompt injection).
- Keep logs of every action, and have a kill switch for each bot.
- Keep kids' accounts separate, with no agent tools.

## Still missing
- Best open **image generation/editing** and **video generation** models, and their VRAM needs
- MiMo-V2.6-Pro serving recipe (exact GPU count)
- Independent check of the claims above

## Part 2 sources
- https://arxiv.org/pdf/2603.05413 (voice pipeline vs all-in-one models)
- https://rits.shanghai.nyu.edu/ai/nvidia-releases-nemotronlabs-voicechat-an-open-full-duplex-voice-model
- https://www.opensourceforu.com/2026/08/nvidia-open-sources-personaplex-built-on-moshi/
- https://www.benchlm.ai/benchmarks/osworld-verified · https://yutori.com/leaderboards/osworld-verified.md
- https://cua.ai/docs/cua/guide · https://pypi.org/project/gui-agents
- https://recipes.vllm.ai/zai-org/GLM-5.3?hardware=b300
- https://www.runpod.io/gpu-cloud/pricing
- https://thenextweb.com/news/openai-dots-always-on-ai-agents-cloud-computers-devday · https://gigazine.net/gsc_news/en/20260812-spacexai-grok-bot/

---

# Part 3: Merged with your research in `private-family-ai-continuation/` (2026-10-27)

Your continuation run checked exact model files and licenses and **corrects several points above**. Where the two disagree, trust your version.

## Corrections to Parts 1-2
| Earlier claim | Corrected |
|---|---|
| "MiMo-V2.6-Pro" | The downloadable model is **`XiaomiMiMo/MiMo-V2.6-Pro-RL`**. Use that exact name and pin a revision. |
| MiMo needs ~1TB at FP8 (guessed from Kimi) | The released files are **~566GB** (mixed MXFP4/FP8). The ggml MXFP4 GGUF is 554GB and the Q2 is 419GB. Memory needed to run it will be higher than the file size. |
| GLM-5.3 753B, fits on 8× H200 | The FP8 files are **~756GB**. Parameter counts differ by source (743-753B). |
| DeepSeek V4.1 Flash 1017 | ~510GB of files. It **accepts images**, so it isn't text-only. |
| Qwen3.8-27B fits a 24-48GB GPU | **Wrong for BF16** (55.6GB). The official FP8 is 30.9GB, so it needs a ~48GB-class GPU. |
| whisper.cpp at `:2022/v1` | The real default is **port 8080, `/inference`**. `:2022` is a separate wrapper. |
| Kokoro, 8 languages | Correct, but **Finnish isn't one of them**. |
| "RL doesn't widen reasoning" was refuted | Not shown. The paper's narrower result still stands. |
| HLE 49.4% / GLM-5.2 SWE-bench Pro 62.1% / Kimi K3 deprecated | **Not verified.** Drop these numbers. |
| Licenses never block personal use | Mostly true, but **Qwen-Image-2.1 is licensed for research/evaluation only**. Moshi has research-use wording, and PersonaPlex is under NVIDIA's terms. |

## Image generation (from your research)
- **FLUX 3 Image Klein** (Oct 15 2026): 5.6B, generates and edits images, up to 10 reference images. It also needs a Qwen3-VL-4B text encoder and a 9B prompt rewriter. Custom license. **The strongest current candidate.**
- **FLUX.2-klein-4B**: Apache 2.0, generates and edits, ~8-13GB. **The safe, simple default.**
- **HiDream-O1-Image**: MIT, strong at editing and keeping subjects consistent. Needs a custom CUDA setup.
- **Qwen-Image-2.1 / Turbo**: excellent, but research-only license. The older Qwen-Image-2512 / Edit-2511 are Apache 2.0.

## Voice (both runs combined)
- Use the pipeline as the base (speech-to-text → LLM → text-to-speech), because it keeps tools, memory and per-person accounts working.
- Speech-to-text: whisper (large-v3 class) through whisper.cpp or faster-whisper. **Qwen3-ASR-1.7B / Parakeet v3** list Finnish.
- Text-to-speech: Kokoro (English) and Qwen3-TTS (expressive, voice cloning). **Finnish:** Piper "Harri" (basic) or **Chatterbox Multilingual** (can clone voices).
- Real-time conversation: **PersonaPlex** (English, full-duplex) or **MiniCPM-o 4.5** (sees and hears at once). **Qwen3-Omni** through vLLM-Omni covers 10 output languages, but not Finnish.
- **No open real-time voice model has verified Finnish support.**

## Vision and documents
- Small baseline: **Qwen3.5-4B**. Stronger: **Qwen3.8-27B-FP8** on a 48GB GPU.
- Documents: a dedicated parser (**Docling/Granite-Docling** or **PaddleOCR-VL-1.6**) is more reliable than a chat model for pulling text out of pages.

## Model sizing strategy (your research's main point)
Start with a smaller everyday model (**Qwen3.6-35B-A3B** as the assistant, **Qwen3-Coder-30B-A3B** for coding). Add MiMo-RL / GLM-5.3 / DeepSeek Flash-1017 on rented servers only for tasks the small model fails.

## Privacy (from your research)
- Open WebUI permissions are additive: one group granting something overrides another group denying it. Start with minimal global permissions.
- **Admins and backup operators can see everything.** Accounts separate family members from each other, not from the admin.
- Deleting a file doesn't remove copies in chats, logs or backups. Test deletion from start to finish.
- Offline mode doesn't block network traffic. Firewall the outgoing traffic separately.

## Still not covered by either run
- **Video generation** (Wan, HunyuanVideo, LTX…)
- Independent check of the agent-bot claims in Part 2 (OSWorld scores, Holo3, Cua, Agent S3)
- Your real hardware, family languages, and number of simultaneous users. These decide the final sizing.

---

# Part 4: Agents, video and Swedish/Finnish/English voice (verified, 2026-10-27)

Research run: 24 sources fetched, 25 claims checked by 3 adversarial reviewers each (23 confirmed, 2 refuted). This part **replaces Part 2's agent and voice notes** wherever they conflict.

## 1. Your own agent bots (like Grok Bot / dots)
| Piece | Pick | Evidence |
|---|---|---|
| Computer layer (one machine per bot) | **Cua** (`trycua/cua`): sandboxes on macOS/Windows/Linux, Lume local VMs, and Cua Driver to control desktop apps and browsers | Actively maintained (licensing notes updated Oct 11 2026). Core is MIT; Cua Spaces and Driver Bench are now FSL-1.1-MIT. The claimed details of Cua's CLI, MCP and gVisor sandboxes were **refuted**, so test these yourself. |
| Computer-control model | **Qwen3.8-27B** (Apache-2.0, sees images, 262K context) | Its own model card claims 84.3 on OSWorld-Verified, above Opus 4.6 Max at 72.7. This is the vendor's own number with no independent check. |
| Alternative model | **Holo4-35B-A3B** (H Company, Sep 2026, ~3B active, cheap to run all the time) | Open weights, reportedly Apache-2.0. **Holo4-27B is reportedly CC BY-NC.** Holo4 replaces the Holo3 mentioned in Part 2. |
| Injection scanner | **BrowseSafe** (Perplexity/Purdue, MIT, built on Qwen3-30B-A3B) | F1 0.904 on its authors' own benchmark (0.788 on attack types it wasn't trained on). Tested on text only, not on images or screenshots. |

**Security, required for anything that touches accounts:**
- No agent is immune to hidden instructions in pages or emails (prompt injection). Anthropic says even a ~1% success rate for attacks is a real risk.
- Use one sandbox or VM per agent, with tokens that only allow what the bot needs.
- Require **human approval to send, buy or delete**.
- Scan raw web and email content with BrowseSafe before the agent sees it (scan the raw text, not summaries). Treat screenshots as unscanned.

**Still unverified:** which framework should handle memory, scheduling and connectors on top (OpenClaw, Hermes Agent, OpenHands, Goose, Agent S3), the sandbox layers E2B, Daytona and RunPod, and a direct comparison with Grok Bot or dots.

## 2. Video generation
Artificial Analysis image-to-video leaderboard for open-weight models (checked Oct 27 2026; Elo is a head-to-head rating, higher is better):
| # | Model | Elo | Notes |
|---|---|---|---|
| 1 | MiniMax H3 (768p, 33B) | 1140 | **Its license reportedly excludes the EU.** Probably not allowed in Sweden or Finland, even for private use. Check the license text. |
| 2 | MAGI-2 Preview (Sand.ai, 114B MoE, video and audio) | 1046 | License not checked yet |
| 3-4 | **LTX-2.5** Fast / Pro (Lightricks, 22B) | 984 / 958 | **Recommended default.** Makes video with synchronized sound from text, an image or a video, can generate several connected scenes in one go, and supports LoRA and fine-tuning. Community license allows private use. ~66GiB download, supports FP8 and offloading. |

**Recommendation:** use **LTX-2.5** as the main video model and try **MAGI-2** for best image-to-video quality once its license checks out. Use H3 only if its license turns out to allow EU use.

**Not covered:** Wan, HunyuanVideo, the text-to-video leaderboard, and comparisons with Veo, Sora or Kling.

## 3. Voice in Swedish, Finnish and English
**Speech-to-text, one model per language:**
| Language | Model | Word error rate (lower is better) on FLEURS test speech |
|---|---|---|
| Swedish | **KBLab/kb-whisper-large** (National Library of Sweden) | 5.4 vs 7.8 for Whisper-large-v3, an average 47% reduction across test sets |
| Finnish | **Finnish-NLP/whisper-large-finnish-v3** (faster-whisper version: `mpasila/faster-whisper-large-finnish-v3`) | 8.21 vs 9.63 after text normalization. One developer's own test, and the test sets may overlap with its training data. |
| English, and detecting which language is spoken | **Whisper-large-v3 / turbo** | — |
| Not recommended for SV/FI | NVIDIA Parakeet v3 / Canary v2 | Worse than Whisper on both. Parakeet: 15.08 Swedish, 13.21 Finnish. |

Route each speaker to the right model: Whisper detects the language, then the Swedish or Finnish model transcribes.

**Text-to-speech and voice cloning:**
- **Chatterbox Multilingual V3** (MIT, 0.5B, lists Swedish and Finnish) clones a voice from a short clip. The clip must be in the same language as the output, or its accent carries over. Setting CFG to 0 reduces this. All output is watermarked by default.
- **There is no measured quality data for Swedish or Finnish.** The claim that one model covers all three languages well was refuted. Listen to it before committing, and keep **Piper** voices (Finnish "Harri", plus Swedish voices) as a fallback.
- English: Kokoro or Chatterbox.

**Real-time voice conversation (no pipeline):** no open model has verified Swedish or Finnish support. Use the pipeline (speech-to-text → LLM → text-to-speech).

## Recommended full stack (as of now)
1. **Brain:** MiMo-V2.6-Pro-RL / GLM-5.3 on rented servers for hard tasks. A smaller Qwen model handles everyday use (Part 3).
2. **Agents:** a Cua VM per bot + Qwen3.8-27B or Holo4-35B-A3B + a BrowseSafe scanner + approval for send, buy and delete
3. **Video:** LTX-2.5 (with sound), with MAGI-2 as an option once its license is checked
4. **Images:** FLUX 3 Klein / FLUX.2-klein-4B (Part 3)
5. **Voice:** Whisper detects the language → KB-Whisper (SV) / Finnish-NLP Whisper (FI) / Whisper-large-v3 (EN) → LLM → Chatterbox Multilingual (test by ear) with Piper as fallback
6. **Front end:** Open WebUI with an account per family member (Part 3 privacy rules)

## Part 4 sources
- https://github.com/trycua/cua
- https://huggingface.co/Qwen/Qwen3.8-27B · https://hub.hcompany.ai/models.md
- https://www.anthropic.com/news/prompt-injection-defenses · https://arxiv.org/abs/2511.20597v1 · https://huggingface.co/perplexity-ai/browsesafe
- https://artificialanalysis.ai/video/leaderboard/image-to-video/open-weights
- https://huggingface.co/Lightricks/LTX-2.5 · https://github.com/Lightricks/LTX-2
- https://huggingface.co/KBLab/kb-whisper-large · https://arxiv.org/abs/2505.17538
- https://huggingface.co/Finnish-NLP/whisper-large-finnish-v3 · https://huggingface.co/mpasila/faster-whisper-large-finnish-v3
- https://arxiv.org/pdf/2509.14128 · https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3
- https://huggingface.co/ResembleAI/chatterbox

---

# Part 5: Remaining gaps (verified, 2026-10-27)

Research run: 23 sources fetched, 25 claims checked by 3 adversarial reviewers each (21 confirmed, 4 refuted).

## Agents
- **Agent S3 / S4** (Simular, Apache-2.0, `simular-ai/Agent-S`): 66% on OSWorld alone, and 72.6% when it picks the best of several attempts (Behavior Best-of-N). Humans score about 72.4%. These are the developer's own numbers.
  - Runs local models through **vLLM**. Ollama should also work through its OpenAI-compatible endpoint.
  - **Still maintained.** GitHub was updated Oct 24 2026, and **Agent S4** came out Oct 20 2026 with OSWorld V2 results using **Qwen3.8-27B**. PyPI has had no new release since Dec 2025, so install from GitHub.
- **Cua**, confirmed again:
  - It controls desktop apps and browsers on Mac, Windows and Linux.
  - It can run on your own machines or your own AWS/GCP/Modal account, using gVisor containers.
  - Agents connect to it through the CLI, MCP or SDKs, and **OpenClaw is listed as a supported agent**.
  - Remote hosts still go through `cua auth login` and a cua.ai relay. Avoid the old `cuabot` npm package, which has security problems.
  - The license changed around Oct 11 2026, and my earlier "mostly MIT" summary was refuted. Read the current LICENSE file before relying on it.

**Agent software that handles memory, scheduling and messaging: still not verified.** These are leads from sources, but the checks didn't confirm them:
- **OpenClaw:** the most popular (~345k stars). It connects to WhatsApp, Telegram and Signal, and has scheduled tasks, MEMORY.md memory, MCP and Ollama support.
  - **Serious 2026 security record:** several CVEs, including token exposure and a sandbox escape, plus the "ClawHavoc" attack that planted hundreds of malicious add-ons in its ClawHub skill store.
  - Microsoft reportedly advised against running it on normal workstations.
- **Hermes Agent** (Nous Research, Feb 2026): searchable memory of all past sessions, isolated profiles, and `hermes mcp serve`. No disclosed security incidents.
- **Practical take:** if you use OpenClaw, run it only inside a Cua or VM sandbox, **install no ClawHub skills**, and keep it fully updated. Hermes looks like the lower-risk choice, but neither has been checked properly.

## Video
| Board (open-weight only) | #1 | #2 | #3 |
|---|---|---|---|
| Text-to-video | MiniMax H3 (Elo ~1158) | LTX-2.5 Fast (~949) | LTX-2.5 Pro (~944) |
| Image-to-video (with sound) | MiniMax H3 (1140) | **MAGI-2 Preview (1046)** | LTX-2.5 Fast (984) |

- **MiniMax H3's license reportedly excludes the EU, UK, US and South Korea.** That most likely rules it out in Sweden and Finland. This comes from secondary reports and I haven't checked the license text myself. DeepLearning.AI also calls H3 "minimally open".
- **Wan and HunyuanVideo aren't on the image-to-video board**, probably because they don't generate sound. Their specs are still not verified.
- Compared with closed models, the only data point is that H3 trails Google's Gemini Omni Flash on the overall board.
- **Pick for Sweden and Finland:** LTX-2.5 is the safe default. MAGI-2 Preview gives the best image-to-video quality, but check its license first.

## Swedish/Finnish voice, final picks
**Speech-to-text:** nothing newer beats the Nordic Whisper models (FLEURS word error rates, lower is better).
| Model | Swedish | Finnish |
|---|---|---|
| **KB-Whisper large** | **5.4** | — |
| **Finnish-NLP whisper-large-finnish-v3** | — | **8.2** |
| Whisper-large-v3 | 7.8–7.9 | 7.7–9.6 |
| Canary-1B-v2 | 9.6 | 8.6 |
| Parakeet v3 | 15.1 | 13.2 |
| Qwen3-ASR-1.7B | 19.4 | 25.2 |

**Text-to-speech:**
- **Finnish: `Finnish-NLP/Chatterbox-Finnish`** (MIT, clones a voice from a short clip). Error rate falls from 28.9% with base Chatterbox to **2.8%**. These are the developer's own numbers, the quality score was rated by an AI rather than people, and the test used only 3 speakers. Part of the training data (Finnish Parliament audio) is under CLARIN terms.
- **Swedish:** no measured result survived (the F5-TTS / Matcha-TTS numbers were refuted). Use **Chatterbox Multilingual** and test it by ear. Keep **Piper** Swedish voices as a fallback.
- **English:** Kokoro or Chatterbox.

## Final recommended stack
| Layer | Pick |
|---|---|
| Brain | MiMo-V2.6-Pro-RL / GLM-5.3 on rented servers for hard tasks; a smaller Qwen model for everyday use |
| Computer-use agent | **Agent S4 + Qwen3.8-27B (via vLLM) inside a Cua sandbox, one per bot**, scanned by BrowseSafe, with your approval for send, buy and delete |
| Always-on assistant (messaging, memory, schedules) | Hermes Agent (lower risk) or OpenClaw, sandboxed with no ClawHub skills. **Not verified.** |
| Video | LTX-2.5 (with sound); MAGI-2 Preview once its license is checked; avoid MiniMax H3 in the EU |
| Images | FLUX 3 Klein / FLUX.2-klein-4B |
| Speech-to-text | Whisper detects the language → KB-Whisper (SV) / Finnish-NLP Whisper (FI) / Whisper-large-v3 (EN) |
| Text-to-speech | Chatterbox-Finnish (FI), Chatterbox Multilingual (SV, test it), Kokoro or Chatterbox (EN) |
| Front end | Open WebUI with an account per family member |

## Part 5 sources
- https://github.com/simular-ai/Agent-S · https://pypi.org/project/gui-agents
- https://github.com/trycua/cua
- https://artificialanalysis.ai/video/leaderboard/text-to-video/open-weights · https://artificialanalysis.ai/video/leaderboard/image-to-video/open-weights
- https://huggingface.co/Finnish-NLP/Chatterbox-Finnish
- https://arxiv.org/html/2505.17538v2 · https://huggingface.co/KBLab/kb-whisper-large
- https://huggingface.co/mpasila/faster-whisper-large-finnish-v3
- https://arxiv.org/pdf/2601.21337 (Qwen3-ASR) · https://arxiv.org/pdf/2509.14128 (Canary/Parakeet)
- Leads that weren't verified: https://thenewstack.io/persistent-ai-agents-compared/ · https://innfactory.ai/en/blog/openclaw-vs-hermes-agent-comparison/
