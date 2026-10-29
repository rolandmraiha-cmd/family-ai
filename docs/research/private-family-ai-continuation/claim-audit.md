# Combined original-claim audit

Research cutoff: 2026-10-26. Verdicts are scoped to each item; repeated claims are not independent votes. Unverified means evidence is insufficient, not that the claim is false.

## 01. Model rankings and coding

[Full research result](results/Model_rankings_and_coding.json)

1. **partially_supported** — MiMo-V2.6-Pro is the strongest open-weight reasoning model right now.

   AA displays it at 46 and BenchLM at 73.6, but the latter is estimated and exact local/API equivalence remains [uncertain]. These are specific composite rankings, not universal proof.

   Sources: [S01](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL), [S09](https://artificialanalysis.ai/models/open-source), [S11](https://artificialanalysis.ai/methodology/intelligence-benchmarking), [S12](https://benchlm.ai/methodology), [S15](https://benchlm.ai/best/open-source).

2. **partially_supported** — MiMo has 1.02T/42B, 1M context, MIT license and September 21-22 weights.

   Official RL card supports architecture/context and MIT metadata; repository creation is September 21. [uncertain] Public launch date and a standalone license text were not established.

   Sources: [S01](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL), [S24](https://huggingface.co/api/models/XiaomiMiMo/MiMo-V2.6-Pro-RL).

3. **unverified** — MiMo Humanity's Last Exam is 49.4%; Kimi K3 is 46.9%.

   [uncertain] The checked MiMo card did not report HLE. Kimi's official HLE-Full no-tools figure is 43.5 with a different with-tools figure, so the quoted 46.9 needs the precise subset, provider and evaluation protocol.

   Sources: [S01](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL), [S05](https://huggingface.co/moonshotai/Kimi-K3).

4. **unverified** — GLM-5.3 is the best agentic coding/tools model.

   Vendor claims strong coding, but differing harnesses and task versions prevent this absolute conclusion. DeepSeek 1017 vendor results are also strong, not a controlled replacement ranking.

   Sources: [S02](https://huggingface.co/zai-org/GLM-5.3/raw/main/README.md), [S03](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017), [S05](https://huggingface.co/moonshotai/Kimi-K3).

5. **partially_supported** — GLM-5.3 is 753B/40B, 1M context, 128K output, text-only.

   Text-only and configured 1M context are supported; [uncertain] recipe parameter counts differ and 128K output was not verified.

   Sources: [S02](https://huggingface.co/zai-org/GLM-5.3/raw/main/README.md), [S10](https://recipes.vllm.ai/zai-org/GLM-5.3), [S14](https://huggingface.co/zai-org/GLM-5.3/raw/main/config.json).

6. **unverified** — GLM-5.2 achieved 62.1% SWE-bench Pro.

   [uncertain] Not established by the checked GLM-5.3 primary table; preserve only with the original exact vendor evaluation citation, task revision and harness.

   Sources: [S02](https://huggingface.co/zai-org/GLM-5.3/raw/main/README.md).

7. **unverified** — Kimi K3 is deprecated and its license disputed.

   Weights remain accessible and exact custom license text is available. [uncertain] No checked official notice established deprecation or a license dispute; API retirement and released-weight availability are separate.

   Sources: [S05](https://huggingface.co/moonshotai/Kimi-K3), [S22](https://huggingface.co/moonshotai/Kimi-K3/raw/main/LICENSE), [S24](https://huggingface.co/api/models/XiaomiMiMo/MiMo-V2.6-Pro-RL).

8. **partially_supported** — Qwen3.8 Max is 2.4T-A95B, text-only, custom license.

   Correct for downloadable Qwen3.8-2.4T-A95B; the hosted Max product adds vision and other capabilities. The original conflates the artifact and service names.

   Sources: [S06](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/README.md), [S23](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE).

9. **partially_supported** — They all expose OpenAI-compatible /v1 APIs through vLLM or SGLang.

   Model-specific recipes support serving integrations, but parser/build/precision support must be pinned. Compatibility does not guarantee all tool, schema or multimodal features; DeepSeek's reference recipe leaves HTTP and execution to callers.

   Sources: [S01](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL), [S03](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017), [S04](https://huggingface.co/stepfun-ai/Step-5-Preview), [S10](https://recipes.vllm.ai/zai-org/GLM-5.3).

10. **unverified** — Nearly every named model released July-October 2026.

   [uncertain] Public launch dates were not reconstructed comprehensively. Repository metadata shows Kimi created in June and Qwen3.6 in April; creation is not public release proof.

   Sources: [S24](https://huggingface.co/api/models/XiaomiMiMo/MiMo-V2.6-Pro-RL).

11. **partially_supported** — None of the licenses blocks personal use.

   Checked grants broadly permit use, but custom terms impose specific commercial and distribution conditions. [uncertain] MiMo's standalone license was not available; avoid a blanket legal assurance.

   Sources: [S19](https://huggingface.co/zai-org/GLM-5.3/raw/main/LICENSE), [S20](https://huggingface.co/stepfun-ai/Step-5-Preview/raw/main/LICENSE.txt), [S21](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/raw/main/LICENSE), [S22](https://huggingface.co/moonshotai/Kimi-K3/raw/main/LICENSE), [S23](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE), [S25](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/blob/main/LICENSE), [S26](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct/blob/main/LICENSE), [S01](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL).

## 02. Vision and documents

[Full research result](results/Vision_and_documents.json)

1. **partially_supported** — Vision / documents: Qwen3.8 27B (Apache 2.0), runners-up Qwen3.6 27B and Qwen3.6 35B-A3B.

   All three official visual repositories and Apache licenses are verified. [uncertain] The universal ordering is not established by independent, task-matched primary evidence; photos, extraction and chart reasoning should be ranked separately.

   Sources: [S01](https://huggingface.co/Qwen/Qwen3.8-27B), [S02](https://huggingface.co/Qwen/Qwen3.6-27B), [S03](https://huggingface.co/Qwen/Qwen3.6-35B-A3B).

2. **refuted** — The 27B vision model fits on a single 24–48GB GPU.

   As an unconditional statement it is wrong: the official BF16 tensors alone need about 55.56 GB / 51.75 GiB. Quantized deployment may be possible under bounded workload assumptions, but was not tested. The vLLM recipe's text-only coverage cannot establish visual fit.

   Sources: [S01](https://huggingface.co/Qwen/Qwen3.8-27B), [S10](https://recipes.vllm.ai/Qwen/Qwen3.8-27B).

3. **partially_supported** — Eyes: Qwen3.8 27B for photos, screenshots and documents.

   General image/video capability is documented. A structured parser is a useful separate component for reliable document retrieval; no single-model acceptance test validates all three household tasks.

   Sources: [S01](https://huggingface.co/Qwen/Qwen3.8-27B), [S07](https://huggingface.co/ibm-granite/granite-docling-258M), [S08](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6), [S09](https://github.com/docling-project/docling).

4. **partially_supported** — Serve each model with vLLM (or SGLang). They all expose OpenAI-compatible /v1 APIs.

   Relevant Qwen cards and GLM recipe provide compatible server interfaces. Software version, processor, precision and architecture support differ. Document tools also have pipeline-specific interfaces; generic API compatibility does not guarantee page conversion or multimodal correctness.

   Sources: [S01](https://huggingface.co/Qwen/Qwen3.8-27B), [S02](https://huggingface.co/Qwen/Qwen3.6-27B), [S03](https://huggingface.co/Qwen/Qwen3.6-35B-A3B), [S08](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6), [S11](https://recipes.vllm.ai/zai-org/GLM-5.3-Flash).

5. **unverified** — Nearly every model above was released July–October 2026.

   [uncertain] Qwen3.6 repository metadata dates to April 2026, while Qwen3.8 metadata dates to August. Repository creation does not establish when weights became public, and this vision subset cannot establish the release distribution of the entire original shortlist. Public release announcements or historical public artifact evidence are needed to confirm or refute the original statement.

   Sources: [S01](https://huggingface.co/Qwen/Qwen3.8-27B), [S02](https://huggingface.co/Qwen/Qwen3.6-27B), [S03](https://huggingface.co/Qwen/Qwen3.6-35B-A3B).

6. **unverified** — Vision is the biggest gap: the best open model ranks #23 of 63 on Roboflow's benchmark.

   [uncertain] No primary, immutable Roboflow evaluation artifact with exact model IDs, date, prompts and leaderboard snapshot was established in this item. Failure to verify does not prove the ranking false; it cannot determine overall vision quality.

   No resolving source established; consult the result limitations.

7. **partially_supported** — None blocks personal use.

   The reviewed Qwen and Paddle weight repositories contain Apache-2.0 text; GLM contains MIT text. That supports permissive personal deployment for these exact artifacts under their terms. It does not prove a blanket statement about every model, dependency or hosted service.

   Sources: [S01](https://huggingface.co/Qwen/Qwen3.8-27B), [S02](https://huggingface.co/Qwen/Qwen3.6-27B), [S03](https://huggingface.co/Qwen/Qwen3.6-35B-A3B), [S04](https://huggingface.co/Qwen/Qwen3.5-4B), [S05](https://huggingface.co/zai-org/GLM-5.3-Flash), [S08](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6).

## 03. Speech recognition and synthesis

[Full research result](results/Speech_recognition_and_synthesis.json)

1. **partially_supported** — Speech-to-text: whisper.cpp is the best open pick.

   It is a real deployable Whisper runtime. It is not a model, and the original report supplies no task-specific comparison proving best recognition quality. Choosing a runtime cannot replace choosing a checkpoint.

   Sources: [S01](https://github.com/openai/whisper), [S02](https://github.com/ggml-org/whisper.cpp).

2. **confirmed** — Kokoro-82M runs on CPU or GPU and supports eight languages.

   The v1.0 card and voice list confirm the count, and the wrapper documents CPU/GPU execution. Quality is voice- and language-dependent; the statement does not include Finnish.

   Sources: [S06](https://huggingface.co/hexgrad/Kokoro-82M), [S07](https://huggingface.co/hexgrad/Kokoro-82M/raw/main/VOICES.md), [S08](https://github.com/remsky/Kokoro-FastAPI/blob/master/README.md).

3. **refuted** — Point STT at whisper.cpp, default :2022/v1.

   As a claim about upstream whisper.cpp defaults, it conflicts with the inspected server code: 8080 and /inference. A separately packaged wrapper could choose 2022 and OpenAI routes, but the original Voice Mode documentation URL could not be fetched, so that wrapper-specific interpretation remains unverified.

   Sources: [S03](https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/examples/server/server.cpp), [S17](https://docs.openwebui.com/features/chat-conversations/audio/speech-to-text/self-hosted-stt/), [S20](https://voice-mode.readthedocs.io/en/stable/installation-tools/).

4. **confirmed** — Point TTS at Kokoro-FastAPI, default :8880/v1.

   The wrapper examples and Open WebUI integration guide use this base URL; the actual speech route is /v1/audio/speech. Container routing and separate audio configuration still apply.

   Sources: [S08](https://github.com/remsky/Kokoro-FastAPI/blob/master/README.md), [S08b](https://raw.githubusercontent.com/remsky/Kokoro-FastAPI/master/docs/integrations/openwebui.md).

5. **refuted** — Serve each model with vLLM or SGLang; all expose OpenAI-compatible /v1 APIs.

   The voice stack includes a C++ engine and a separate TTS wrapper. Neither universal vLLM/SGLang support nor universal audio-protocol equivalence follows from /v1. Qwen ASR chat-completion input and WebUI multipart transcription require different contracts.

   Sources: [S03](https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/examples/server/server.cpp), [S08](https://github.com/remsky/Kokoro-FastAPI/blob/master/README.md), [S09](https://github.com/QwenLM/Qwen3-ASR), [S12](https://docs.vllm.ai/projects/vllm-omni/en/stable/serving/speech_api/), [S17](https://docs.openwebui.com/features/chat-conversations/audio/speech-to-text/self-hosted-stt/).

6. **partially_supported** — Use the STT to LLM to TTS pipeline instead of unverified speech-to-speech.

   Modular components and integration routes exist and permit separate testing. This report did not establish comparative end-to-end speech-to-speech quality, and modular serving alone does not deliver interruption, echo control or semantic turn-taking.

   Sources: [S04](https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/examples/stream/README.md), [S08](https://github.com/remsky/Kokoro-FastAPI/blob/master/README.md), [S16](https://github.com/snakers4/silero-vad), [S17](https://docs.openwebui.com/features/chat-conversations/audio/speech-to-text/self-hosted-stt/).

7. **partially_supported** — None of the licenses blocks personal use.

   The reviewed Whisper and Kokoro components use permissive licenses compatible with ordinary local use, subject to notices. Voice files, third-party data and cloning permissions must be checked separately; this conclusion cannot be extended to every model in the original report.

   Sources: [S01](https://github.com/openai/whisper), [S02](https://github.com/ggml-org/whisper.cpp), [S06](https://huggingface.co/hexgrad/Kokoro-82M), [S08](https://github.com/remsky/Kokoro-FastAPI/blob/master/README.md), [S13](https://github.com/OHF-Voice/piper1-gpl), [S14](https://huggingface.co/rhasspy/piper-voices/raw/main/fi/fi_FI/harri/medium/MODEL_CARD).

## 04. Speech-to-speech and omni

[Full research result](results/Speechtospeech_and_omni.json)

1. **confirmed** — Speech-to-speech: Not verified.

   This accurately described the original report's evidence gap. The continuation now establishes multiple downloadable native audio candidates; it is no longer an unresolved existence question.

   Sources: [S01](https://github.com/kyutai-labs/moshi), [S03](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct), [S05](https://github.com/stepfun-ai/Step-Audio2), [S07](https://huggingface.co/nvidia/personaplex-7b-v1), [S09](https://github.com/OpenBMB/MiniCPM-V/blob/main/docs/minicpm_o4dot5_en.md), [S11](https://github.com/XiaomiMiMo/MiMo-Audio), [S14](https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B).

2. **unverified** — Open models were far behind closed ones in older data.

   No dated comparable benchmark/harness was supplied. Current primary reports contain task-specific vendor comparisons, sometimes near or above named closed baselines, but do not establish universal parity or superiority.

   Sources: [S04](https://arxiv.org/abs/2509.17765v1), [S06](https://arxiv.org/html/2507.16632v2), [S13](https://arxiv.org/html/2512.23808v1).

3. **partially_supported** — Use the STT → LLM → TTS pipeline instead.

   Still a reasonable tool/memory integration default and component-level fallback, not evidence that native speech is unavailable or always worse.

   Sources: [S02](https://huggingface.co/kyutai/moshiko-pytorch-bf16), [S16](https://github.com/ggml-org/whisper.cpp), [S17](https://huggingface.co/hexgrad/Kokoro-82M).

4. **refuted** — Serve each model with vLLM or SGLang; they all expose OpenAI-compatible /v1 APIs.

   As a universal claim it is false: Moshi documents its own streaming framework/server, and Step requires specialized parsers/backends. Qwen audio output is documented in vLLM-Omni; ordinary text-server compatibility cannot be generalized to native duplex audio.

   Sources: [S01](https://github.com/kyutai-labs/moshi), [S05](https://github.com/stepfun-ai/Step-Audio2), [S20](https://vllm-project.github.io/2026/07/01/qwen3-omni-optimization.html).

5. **partially_supported** — None blocks personal use.

   Permissive licenses are common, but models differ: Moshi has research-only intended-use wording alongside CC BY weights; PersonaPlex requires NVIDIA terms; LFM has a custom revenue-conditioned license; MiMo's MIT card lacks a fetched standalone weight-license file. No universal legal clearance follows.

   Sources: [S02](https://huggingface.co/kyutai/moshiko-pytorch-bf16), [S07](https://huggingface.co/nvidia/personaplex-7b-v1), [S12](https://huggingface.co/XiaomiMiMo/MiMo-Audio-7B-Instruct), [S15](https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B/raw/main/LICENSE), [S18](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/), [L02](https://raw.githubusercontent.com/XiaomiMiMo/MiMo-Audio/main/LICENSE).

## 05. Image generation and editing

[Full research result](results/Image_generation_and_editing.json)

1. **partially_supported** — Image generation: Not verified. No claim survived checking; follow up FLUX / Qwen-Image / HiDream.

   The report correctly labels its own image section unresolved. The unseen earlier voting process cannot be audited. Current primary sources now establish released local candidates; absence of earlier verified claims was not evidence that no useful model existed.

   Sources: [S01](https://bfl.ai/blog/flux-3-image-klein), [S07](https://github.com/QwenLM/Qwen-Image-2.1), [S15](https://github.com/HiDream-ai/HiDream-O1-Image), [S19](https://github.com/HiDream-ai/HiDream-I1).

2. **partially_supported** — Best open image-generation model and the VRAM it needs remain open questions.

   Conditional candidates and workload-specific memory evidence can now be supplied. A single best model or universal minimum remains unsupported because licenses, text fidelity, edit preservation, precision and workload differ.

   Sources: [S01](https://bfl.ai/blog/flux-3-image-klein), [S06](https://bfl.ai/models/flux-2-klein), [S10](https://raw.githubusercontent.com/QwenLM/Qwen-Image-2.1/main/LICENSE), [S21](https://recipes.vllm.ai/Qwen/Qwen-Image-2.1), [S26](https://huggingface.co/blog/flux-3).

3. **partially_supported** — Serve each model with vLLM (or SGLang). They all expose OpenAI-compatible /v1 APIs.

   This cannot be generalized to image engines. FLUX 3 has Diffusers/ComfyUI integrations; Qwen 2.1 support requires checking the diffusion-specific runtime and release. HiDream O1 documents its custom CUDA pipeline. API path compatibility does not prove image model support.

   Sources: [S02](https://github.com/black-forest-labs/flux-3-image-klein), [S07](https://github.com/QwenLM/Qwen-Image-2.1), [S15](https://github.com/HiDream-ai/HiDream-O1-Image), [S21](https://recipes.vllm.ai/Qwen/Qwen-Image-2.1).

4. **unverified** — Check each model's license. None blocks personal use.

   The original statement concerned a different list without an image pick, so it cannot be retrospectively refuted for every listed model here. It must not be extended to this continuation: Qwen 2.1 permits research/evaluation rather than all personal activity, and FLUX custom licenses impose conditions absent from Apache/MIT.

   Sources: [S10](https://raw.githubusercontent.com/QwenLM/Qwen-Image-2.1/main/LICENSE), [S27](https://huggingface.co/black-forest-labs/flux-3-image-klein/blob/main/LICENSE.md), [S23](https://raw.githubusercontent.com/black-forest-labs/flux2/main/model_licenses/LICENSE-FLUX-NON-COMMERICAL).

## 06. Hardware and serving

[Full research result](results/Hardware_and_serving.json)

1. **partially_supported** — Kimi full weights: about 610 GB.

   Official native INT4 shards total 595.178 GB; Unsloth BF16 main GGUF is 2,053.156 GB. Rough compressed storage and full precision are different quantities.

   Sources: [S05](https://huggingface.co/moonshotai/Kimi-K2.6), [S06](https://huggingface.co/unsloth/Kimi-K2.6-GGUF).

2. **confirmed** — Kimi UD-Q2 340-350 GB, Q4 about 584 GB, Q8 about 595 GB.

   Main GGUF metadata gives 340.477, 583.711 and 594.545 GB. Projector and runtime state are additional.

   Sources: [S06](https://huggingface.co/unsloth/Kimi-K2.6-GGUF).

3. **partially_supported** — MiMo about 1 TB+ FP8 or 350-600 GB quantized, inferred from Kimi.

   Ideal all-FP8 arithmetic is 1.02 TB, but the released artifact uses mixed MXFP4 storage. Verified main GGUFs are 418.769/554.212 GB. [uncertain] No checked MiMo artifact establishes the 350 GB lower bound or resident fit.

   Sources: [S01](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL), [S07](https://huggingface.co/ggml-org/MiMo-V2.6-Pro-RL-GGUF).

4. **partially_supported** — Requires eight H200/B200-class GPUs or several Macs.

   Serving examples exist, including explicit GLM hardware. [uncertain] No universal GPU count or usable Mac cluster is established; context, precision, concurrency and interconnect matter.

   Sources: [S01](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL), [S08](https://recipes.vllm.ai/zai-org/GLM-5.3), [S12](https://ml-explore.github.io/mlx/build/html/usage/unified_memory.html).

5. **refuted** — 27B vision fits a single 24-48 GB GPU.

   Unqualified fit is false for BF16: stored tensors are 55.563 GB. Official FP8 is 30.867 GB; 24 GB needs another quantization/offload/smaller model. [uncertain] Exact 24 GB vision fit unproven.

   Sources: [S04](https://huggingface.co/Qwen/Qwen3.8-27B), [S08](https://recipes.vllm.ai/zai-org/GLM-5.3).

6. **partially_supported** — Serve every model with vLLM or SGLang; all expose /v1.

   API compatibility does not establish exact artifact support, tools, modalities or kernels. Model-specific versions and parsers remain necessary.

   Sources: [S08](https://recipes.vllm.ai/zai-org/GLM-5.3), [S09](https://github.com/vllm-project/vllm/blob/33a73daf1771eaa1014d1f272b4ae6815ee62d7e/vllm/model_executor/models/registry.py), [S11](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/).

## 07. Customization and abliteration

[Full research result](results/Customization_and_abliteration.json)

1. **partially_supported** — LoRA forgets less general ability, with 0.617 versus 0.545 retention, and learns less, with HumanEval 0.224 versus 0.263.

   F1 verifies the values and their specific experimental setting. Calling the raw source-task average retention and generalizing across adaptation regimes is misleading.

   Sources: [S01](https://arxiv.org/html/2405.09673v2).

2. **partially_supported** — LoRA is the safe choice for persona, style and family-specific knowledge.

   Parameter-efficient style adaptation is a plausible candidate, but the cited code/math study is not a family-persona or privacy trial. Family records require update, access and deletion controls; safety is not guaranteed by adapter rank.

   Sources: [S01](https://arxiv.org/html/2405.09673v2), [S10](https://arxiv.org/abs/2012.07805), [S13](https://github.com/huggingface/peft/releases/tag/v0.17.0).

3. **confirmed** — Distillation from a stronger teacher can widen a smaller model's reasoning.

   Supported as an existential, conditional claim by teacher-student training results and the coverage comparison in F2/F3; not a guarantee of improvement on every task or model.

   Sources: [S02](https://arxiv.org/html/2504.13837v5), [S03](https://arxiv.org/html/2501.12948v1).

4. **unverified** — The RL-does-not-expand-reasoning claims were refuted in verification.

   No reproducible refutation protocol is supplied in the report. The cited study maintains its scoped empirical conclusion in v5. F4 offers different positive generalization evidence, not a direct overturning of the same experiment.

   Sources: [S02](https://arxiv.org/html/2504.13837v5), [S04](https://arxiv.org/html/2501.17161v2).

5. **unverified** — Prompts, RAG and tools usually beat fine-tuning the flagship.

   A reasonable low-cost project sequence is not a measured universal ranking. No matched flagship/family-workload comparison supports the word usually in the supplied report.

   Sources: [S08](https://arxiv.org/abs/2005.11401), [S09](https://arxiv.org/abs/2307.03172).

6. **partially_supported** — How much reasoning quality abliteration costs on 2026 MoE models is not verified.

   A universal reasoning-loss estimate remains unavailable. F7 adds relevant dated MoE behavioral evidence, but not the named flagship models or a general reasoning benchmark.

   Sources: [S05](https://arxiv.org/html/2406.11717v3), [S06](https://scholarship.miami.edu/esploro/outputs/conferencePaper/Auditing-Abliteration-Normalization-Placement-Edit-Budget/991033194041902976), [S07](https://arxiv.org/html/2607.17427v1).

7. **unverified** — No model license blocks personal use.

   The blanket claim is not established by this adaptation audit. Code, base weights, derivatives, source data and teacher outputs require separate checks; a permissive tool license does not grant rights in private records.

   Sources: [S13](https://github.com/huggingface/peft/releases/tag/v0.17.0), [S14](https://github.com/deepseek-ai/DeepSeek-R1).

## 08. Private family deployment

[Full research result](results/Private_family_deployment.json)

1. **partially_supported** — Serve each model with vLLM/SGLang; all expose OpenAI-compatible /v1 APIs.

   vLLM documents this connection pattern. Model support and non-chat modalities/tool schemas need individual verification; no universal compatibility established here.

   Sources: [S12](https://docs.vllm.ai/en/latest/deployment/frameworks/open-webui/).

2. **confirmed** — Open WebUI can point OPENAI_API_BASE_URL to the vLLM /v1 endpoint.

   Documented integration, with environment/persisted configuration and container networking to verify in a deployment.

   Sources: [S12](https://docs.vllm.ai/en/latest/deployment/frameworks/open-webui/), [S13](https://docs.openwebui.com/reference/env-configuration/).

3. **refuted** — whisper.cpp STT default is :2022/v1.

   Upstream server documentation instead specifies port 8080 and /inference. Another wrapper may use 2022, but that is not the upstream default.

   Sources: [S14](https://github.com/ggml-org/whisper.cpp/blob/master/examples/server/README.md).

4. **confirmed** — Kokoro-FastAPI default is :8880/v1.

   README documents this base and speech/voices endpoints; voice selection and reachability are additional configuration.

   Sources: [S15](https://github.com/remsky/Kokoro-FastAPI).

5. **partially_supported** — Add family accounts, memory and document search inside Open WebUI.

   Features exist in inspected docs, but accounts alone do not establish tested isolation or privacy from administrators.

   Sources: [S01](https://docs.openwebui.com/features/authentication-access/rbac/permissions/), [S02](https://docs.openwebui.com/security/chat-data-privacy-and-encryption/), [S03](https://docs.openwebui.com/features/chat-conversations/memory/), [S04](https://docs.openwebui.com/features/workspace/knowledge/).

6. **partially_supported** — Local front end plus local models constitutes private deployment.

   All processing stages, plugins, clients, logs and remote services need a data-flow audit and separate egress control.

   Sources: [S06](https://docs.openwebui.com/tutorials/maintenance/offline-mode/).

7. **unverified** — None of the models' licenses blocks personal use.

   This blanket statement cannot be inferred across the original report's unaudited checkpoints. This item verifies selected component terms only.

   Sources: [S10](https://github.com/open-webui/open-webui/blob/main/LICENSE), [S23](https://huggingface.co/Qwen/Qwen3-8B/raw/main/LICENSE), [S24](https://huggingface.co/hexgrad/Kokoro-82M), [S25](https://raw.githubusercontent.com/remsky/Kokoro-FastAPI/master/LICENSE), [S26](https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/LICENSE), [S27](https://raw.githubusercontent.com/vllm-project/vllm/main/LICENSE).
