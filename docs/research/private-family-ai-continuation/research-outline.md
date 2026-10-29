# Research outline: private family AI continuation

Research date and cutoff: **2026-10-26**.

Continue [the original report](../open-model-research-2026-10.md), auditing its recommendations and resolving deployment gaps. Preserve the original as a historical input. The user approved this scope and the execution defaults.

## Research questions

| Item | Main questions | Assigned result |
|---|---|---|
| 1. Model rankings and coding | Which exact open-weight checkpoints exist? What do comparable reasoning, coding and tool-use evaluations establish? Which smaller alternatives merit local evaluation? | [Model rankings and coding](results/Model_rankings_and_coding.json) |
| 2. Vision and documents | Which models support photos, screenshots, OCR, layouts and charts? What precision and runtime constraints affect local use? | [Vision and documents](results/Vision_and_documents.json) |
| 3. Speech recognition and synthesis | Which ASR/TTS models and serving implementations are suitable? What language, streaming and licensing evidence exists? | [Speech recognition and synthesis](results/Speech_recognition_and_synthesis.json) |
| 4. Speech-to-speech and omni | What native audio options actually support streaming and interruption? How do they compare with an ASR–LLM–TTS pipeline? | [Speech-to-speech and omni](results/Speechtospeech_and_omni.json) |
| 5. Image generation and editing | Which exact FLUX, Qwen-Image, HiDream or other verified variants suit generation and editing? What are their licenses and memory requirements? | [Image generation and editing](results/Image_generation_and_editing.json) |
| 6. Hardware and serving | What memory and backend support are documented? How do weight precision, KV cache, context, concurrency and offloading change capacity? | [Hardware and serving](results/Hardware_and_serving.json) |
| 7. Customization and abliteration | What do prompting, retrieval, LoRA, distillation and RL improve? What evidence supports retention claims and quality effects from refusal removal? | [Customization and abliteration](results/Customization_and_abliteration.json) |
| 8. Private family deployment | How should accounts, retrieval, memory, voice, tools, privacy and recovery fit together? What conditions determine an appropriate stack? | [Private family deployment](results/Private_family_deployment.json) |

English and Finnish are evaluation examples; language requirements, available hardware, budget and number of simultaneous users have not been supplied.

## Shared evidence requirements

Each result must cover all 17 fields defined in [fields.yaml](fields.yaml): identity and scope; verified findings; candidate comparison; deployment requirements; operating profile; language evidence; retrieval and memory implications; original-claim audit; benchmark caveats; evaluation plan; privacy and licensing; recommendations; next steps; unresolved questions; sources.

- Read primary sources: publisher model cards and licenses, original papers, implementation repositories, and official runtime documentation.
- Identify exact artifacts, revisions and source dates where available.
- Distinguish publisher-reported measurements, independent evaluations, arithmetic estimates and unknowns.
- Cite source IDs next to findings and include a source ledger with direct links.
- Audit original claims as confirmed, partially supported, refuted or unverified. Missing evidence alone does not establish falsity.
- Mark uncertain values with `[uncertain]` and list the affected fields in the final `uncertain` array.
- Propose local evaluation and acceptance tests. This research run does not measure model quality, memory fit or latency.

## Preliminary web supplement

A separate web researcher checked the initial framework and added:

1. Embeddings, rerankers and document grounding, prompted by the [Qwen3 Embedding release](https://qwenlm.github.io/blog/qwen3-embedding/).
2. Tool calling and structured outputs, using the [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard) as a methodological lead.
3. Useful long-context performance, rather than advertised context alone, using [RULER](https://arxiv.org/abs/2404.06654).
4. Component-level data flow, user permissions and operator access, using [Open WebUI permissions](https://docs.openwebui.com/features/authentication-access/rbac/permissions/) and [hardening documentation](https://docs.openwebui.com/getting-started/advanced-topics/hardening/).
5. Version pinning, upgrades and restoration, using [Open WebUI update guidance](https://docs.openwebui.com/getting-started/updating/).
6. Separate prefill, generation and end-to-end latency evaluation, using [llama.cpp benchmark documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/bench/speed-bench/README.md).

These are research leads, not evidence that any specific candidate passes the proposed tests. Living documentation may lack a publication date or historical revision.

## Execution

[outline.yaml](outline.yaml) is the machine-readable plan. Use one independent `web_researcher` per item, in batches of at most three. The user requested both stages and approved these defaults.

Save substantive results under `results/`; keep agent chat output to completion/status messages. Validate complete field coverage using the research skill's supplied validator, then check the expected file count, source ledgers and uncertainty markers. Resume only from complete, valid results.

This is research only: no deployment, purchases, model downloads, package installation or training.
