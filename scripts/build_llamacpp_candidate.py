"""Write a reviewable experiment config; this does not deploy or submit jobs."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Use the exact Hub release reference: registry authentication failed with @digest.
# Observed image digest: 750cfe205937664fee301fe7959f1e6ff5fbe938d117113b3cc21158c72e13c1.
IMAGE = "registry.runpod.net/eniewold-llama-cpp-runpod-master-dockerfile:0365854c9"
REGIONS = ["EU-SE-1", "EUR-IS-2", "EU-CZ-1", "EU-RO-1", "EU-NL-1", "EU-FR-1", "EUR-NO-1", "EUR-IS-3", "EUR-IS-4"]
MODELS = {
    "q8": ("ggml-org/gemma-4-31B-it-GGUF", "3d47a7e680fb9526dcac74335858f0f31acc9c27"),
    "qat-q4": ("google/gemma-4-31B-it-qat-q4_0-gguf", "59dde24573e7e61570dba08b18a2e1fe246955ed"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--profile", choices=["q8", "qat-q4"], default="q8")
    options = parser.parse_args()
    config = json.loads((ROOT / "runpod/gemma-endpoint.json").read_text())
    config.update(image=IMAGE, dataCenterIds=REGIONS,
                  entrypoint=["python", "-u", "-c", (ROOT / "runpod/llamacpp_worker.py").read_text()], cmd=[])
    config["gpu"]["minCudaVersion"] = "12.8"
    repo, revision = MODELS[options.profile]
    config["env"]["MODEL_NAME"] = repo
    config["env"]["FAMILY_GGUF_PROFILE"] = options.profile
    if options.profile == "qat-q4":
        config["gpu"]["pools"] = ["AMPERE_24", "ADA_24", "AMPERE_48", "ADA_48_PRO"]
    # Full environment is retained, including MAX_NUM_BATCHED_TOKENS=8192.
    # Generate disabled, so applying the file cannot accidentally start a worker.
    config["workers"]["min"] = 0
    config["workers"]["max"] = 0
    options.output.write_text(json.dumps(config, indent=2) + "\n")
    # REST v2/env changes do not update the separate model-store attachment.
    # Keep this plan separate from the REST body; it needs a full GraphQL
    # round trip (or runpodctl serverless update --model-reference).
    cache_plan = options.output.with_suffix(".model-cache.json")
    cache_plan.write_text(json.dumps({"endpointId": config["id"],
        "modelReferences": ["https://huggingface.co/" + repo + ":" + revision],
        "workersMustBeStopped": True}, indent=2) + "\n")
    print("Prepared disabled candidate:", options.output)
    print("Separate pinned cache attachment required:", cache_plan)


if __name__ == "__main__":
    main()
