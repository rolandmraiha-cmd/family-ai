"""Build self-contained imports; originals stay readable/testable in this repo.

Open WebUI loads each plugin as an isolated Python module. Bundling the shared
source avoids pip installs, network bootstraps, extra services or copied secrets.
The shared SQLite path keeps admission atomic across those isolated modules.
"""
import ast
import json
from pathlib import Path
import sys


def build(root, output):
    core = (root / "family_backend/control.py").read_text()
    api = (root / "family_backend/api.py").read_text()
    definitions = [
        ("family_router", "Family AI Router", "functions/family_router.py", False),
        ("family_start_voice", "Start voice", "actions/start_voice.py", False),
        ("family_runtime", "Family AI backend lifecycle", "events/family_runtime.py", True),
        ("family_media", "Family Modules (reasoning, images and video)", "tools/family_media.py", False),
    ]
    functions, tools = [], []
    output.mkdir(parents=True, exist_ok=True)

    def inline_imports(source):
        lines = source.splitlines(keepends=True)
        for node in reversed(ast.parse(source).body):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("family_backend"):
                del lines[node.lineno - 1:node.end_lineno]
        return "".join(lines)

    for identifier, title, path, include_api in definitions:
        original = (root / "openwebui" / path).read_text()
        docstring = ast.get_docstring(ast.parse(original)) or ""
        # Keep the plugin frontmatter as the first docstring; control's prose
        # docstring must not become its frontmatter.
        tree = ast.parse(original)
        first = tree.body[0]
        body = "".join(original.splitlines(keepends=True)[first.end_lineno:])
        source = '"""\n' + docstring + '\n"""\n\n' + core + "\n"
        if include_api:
            source += inline_imports(api) + "\n"
        source += inline_imports(body)
        compile(source, identifier, "exec")
        (output / f"{identifier}.py").write_text(source)
        entry = {"id": identifier, "name": title, "content": source, "meta": {"description": title}}
        (tools if identifier == "family_media" else functions).append(entry)
    (output / "functions.json").write_text(json.dumps(functions, ensure_ascii=False))
    (output / "tools.json").write_text(json.dumps(tools, ensure_ascii=False))
    return {"functions": [f["id"] for f in functions], "tools": [t["id"] for t in tools]}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(build(root, Path(sys.argv[1]) if len(sys.argv) > 1 else root / "dist/openwebui")))
