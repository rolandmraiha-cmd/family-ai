# Private family AI: research continuation

**Research cutoff: 2026-10-26.** This continues the original report with exact-artifact checks and practical deployment evidence.

The evidence supports a conditional, measured choice of components. It does not establish one universally best open-weight family stack. Start evaluation with hardware you already have, a smaller supported assistant, modular voice, and explicit account/document boundaries; compare larger or native-audio options only where they improve the required tasks.

## Main corrections

- **Model names need exact checkpoint mappings.** MiMo's ranking/display name maps to an RL artifact, while hosted Qwen3.8-Max and downloadable Qwen3.8-2.4T-A95B differ. Benchmark results cannot automatically transfer between them. See the [model audit](results/Model_rankings_and_coding.json), [MiMo artifact](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL), and [Qwen artifact](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B).
- **The blanket 24–48 GB vision claim fails for BF16.** Qwen3.8-27B's official BF16 tensors total approximately 55.56 GB; the official FP8 variant is approximately 30.87 GB before runtime state. Quantized/offloaded fit and visual latency still require testing. The text-only vLLM recipe does not establish vision support or fit. See the [hardware accounting](results/Hardware_and_serving.json), [official artifacts](https://huggingface.co/Qwen/Qwen3.8-27B), and [runtime recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B).
- **Large-model download sizes and serving memory are different.** Hub metadata for MiMo's main released shards totals about 566.05 GB and describes mixed low-bit storage; this replaces a Kimi-based proxy. KV cache, repacking, activations, runtime state and concurrency remain additional. See [hardware evidence and exact revisions](results/Hardware_and_serving.json).
- **Voice engines and model checkpoints must be named separately.** whisper.cpp is an engine. Its inspected upstream defaults are port 8080 and `/inference`; the original `:2022/v1` route requires a separately identified wrapper. Kokoro's eight-language count is supported, with no Finnish in that list. See the [voice result](results/Speech_recognition_and_synthesis.json), [upstream server source](https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/examples/server/server.cpp), and [Kokoro voice list](https://huggingface.co/hexgrad/Kokoro-82M/raw/main/VOICES.md).
- **Native audio exists, but audio input/output does not prove interruption support.** Moshi, PersonaPlex, Qwen3-Omni, MiniCPM-o and other verified candidates deserve task-specific comparison. Vendor demonstrations do not establish household latency or universal parity with closed models. See [native-audio evidence](results/Speechtospeech_and_omni.json).
- **Image licenses change the shortlist.** FLUX.2-klein-4B is a permissive practical evaluation candidate. Newer FLUX 3 and HiDream-O1 variants merit comparison under their exact terms and runtime requirements. Qwen-Image-2.1's research-only grant prevents an unqualified everyday-use recommendation. See the [image result](results/Image_generation_and_editing.json), [FLUX.2 weight license](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/blob/main/LICENSE.md), and [Qwen research license](https://raw.githubusercontent.com/QwenLM/Qwen-Image-2.1/main/LICENSE).
- **Adaptation claims need their experimental scope.** The quoted LoRA values come from a specific Llama-2-7B code-training experiment; the source-task average is not a universal retention rate. RL papers examine different capability/generalization questions, so the report's assertion that a contrary claim was “refuted” is unsupported. Abliteration evidence shows model- and task-dependent effects, without a transferable flagship-MoE quality-loss figure. See the [customization audit](results/Customization_and_abliteration.json), [LoRA study](https://arxiv.org/html/2405.09673v2), [RL coverage study](https://arxiv.org/html/2504.13837v5), and [2026 MoE study](https://arxiv.org/html/2607.17427v1).
- **Accounts and local inference do not establish complete privacy.** Open WebUI documents additive permissions and per-user features, while backend operators remain trusted. Check every processing stage, external connection, deletion path and backup; offline mode alone does not enforce network isolation. See the [deployment result](results/Private_family_deployment.json), [permissions](https://docs.openwebui.com/features/authentication-access/rbac/permissions/), [offline documentation](https://docs.openwebui.com/tutorials/maintenance/offline-mode/), and [backup guidance](https://docs.openwebui.com/tutorials/maintenance/backups/).

## Conditional shortlist

These are candidates for controlled evaluation, not measured winners or confirmed fits.

| Area | Initial evaluation choice | When to compare a stronger or different option |
|---|---|---|
| General assistant and coding | A supported smaller checkpoint; Qwen3.6-35B-A3B and Qwen3-Coder-30B-A3B-Instruct are documented comparison candidates if their exact representation fits. | Compare pinned MiMo RL, GLM-5.3 and DeepSeek Flash-1017 under one harness after establishing server capacity. [Details](results/Model_rankings_and_coding.json) |
| Vision and documents | Qwen3.5-4B visual baseline plus a structured extraction path such as Docling/Granite-Docling or PaddleOCR-VL. | Compare compatible quantized Qwen3.8-27B on difficult pages, charts and screenshots; require measured multimodal memory. [Details](results/Vision_and_documents.json) |
| Modular voice | A named Whisper checkpoint through a maintained engine, plus Kokoro for supported languages. | Compare Qwen3-ASR/Parakeet or other documented ASR; evaluate language-appropriate TTS separately. Finnish requires a different synthesis shortlist. [Details](results/Speech_recognition_and_synthesis.json) |
| Native audio | Keep the modular path as the tool/retrieval integration baseline. | Evaluate PersonaPlex/Moshi for English duplex, MiniCPM-o for documented visual/audio duplex, or Qwen3-Omni for its supported modalities and languages. Verify actual interruption handling. [Details](results/Speechtospeech_and_omni.json) |
| Images | FLUX.2-klein-4B as a permissive generation/editing baseline. | Compare FLUX 3 or HiDream-O1 variants when quality gains, terms and measured runtime justify them; retain older permissive Qwen image variants as relevant baselines. [Details](results/Image_generation_and_editing.json) |
| Hardware | Use existing hardware with a supported smaller model; specify precision, context and concurrency before sizing. | Server-scale models need exact format/kernel support and per-rank memory tests. File bytes and advertised active parameters do not prove usable speed. [Details](results/Hardware_and_serving.json) |
| Customization | Explicit instructions and access-controlled external records; keep an unmodified baseline. | Consider a reversible LoRA experiment for a demonstrated style/format gap. Distillation, RL and refusal removal require separate evidence and regression evaluation. [Details](results/Customization_and_abliteration.json) |
| Private deployment | Separate accounts, supported local inference, local extraction/retrieval, explicit private/shared stores and optional modular voice. | Prove account boundaries, operator trust, egress limits, deletion and restoration before relying on privacy. Qwen3 Embedding/Reranker 0.6B are leads to compare with simpler retrieval baselines. [Details](results/Private_family_deployment.json) |

## Proposed next steps

1. Record the existing CPU/GPU/RAM, required languages, expected simultaneous users, privacy boundary and acceptable response delay. These inputs remain unknown.
2. Pin one small baseline stack, including exact model revisions, licenses, quantizations, runtime versions and parsers.
3. Use held-out representative household tasks: ordinary chat, documents with known answers, charts/screenshots, voice in noise, interruptions and controlled tool calls. Measure errors and grounding alongside cold start, time to first token/audio, peak memory and concurrent load.
4. Test two accounts against direct document, memory and API access; test malicious instructions inside retrieved documents; inspect network egress; demonstrate deletion and a consistent backup restore. Administrators and backup operators remain part of the trust model.
5. Compare one stronger candidate only for categories the baseline fails. Make adaptation a separate experiment with an unchanged regression baseline.

These are proposed evaluations. None ran during this research.

## Evidence limits and verification

The initial framework was supplemented by one web researcher. Each of the eight approved outline items was then assigned to a separate `web_researcher`, in batches of three, three and two. The user approved the scope and defaults. Substantive outputs are in [results/](results/); [outline.yaml](outline.yaml) and [fields.yaml](fields.yaml) record the plan and shared definitions.

Each result has 17 required fields, an original-claim audit, a source ledger, recommendations and explicitly marked uncertainties. The [combined claim audit](claim-audit.md) preserves item-specific verdicts; repeated claims are not independent verification votes. The [run manifest](run-manifest.json) records validation results and artifact hashes.

The supplied research validator checks field coverage, not factual truth. Additional checks cover the eight expected result files, JSON parsing, source-ID integrity, ledger URL syntax and uncertainty-label consistency. Source conclusions were reviewed during synthesis. One vision audit verdict was corrected to “unverified”: repository creation dates alone cannot establish public release dates.

The original report's claimed voting run could not be reconstructed from the single input file. This continuation does not claim to repeat it. Live documentation can change, missing publication dates remain flagged, and publisher benchmark figures are identified separately from independent measurements. No local model quality, usable hardware fit, throughput or end-to-end privacy was empirically established.

The original report is preserved. No weights were downloaded, no models trained or deployed, and no paid infrastructure was activated.
