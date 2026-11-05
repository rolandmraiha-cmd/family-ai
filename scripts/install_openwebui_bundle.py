"""Install reviewed plugins inside the existing Open WebUI container, as its admin.

Run with a bundle directory argument. Does not create tokens, change accounts,
copy credentials, alter defaults or contact a provider. Existing content/valves
are preserved unless the corresponding reviewed plugin source changes.
"""
import asyncio
import json
import os
from pathlib import Path
import sqlite3
import sys
import types


async def install(bundle):
    # start.sh exports this only to the app process; docker exec has a fresh
    # environment. Read the same existing file in memory, never print/copy it.
    if not os.environ.get("WEBUI_SECRET_KEY"):
        secret_file = Path(os.environ.get("WEBUI_SECRET_KEY_FILE", "/app/backend/data/.webui_secret_key"))
        os.environ["WEBUI_SECRET_KEY"] = secret_file.read_text().strip()
    from open_webui.models.functions import Functions, FunctionForm
    from open_webui.models.tools import Tools, ToolForm
    from open_webui.models.models import Models, ModelForm
    from open_webui.utils.tools import get_tool_specs
    from open_webui.utils.plugin import extract_frontmatter

    database = Path(os.environ.get("DATA_DIR", "/app/backend/data")) / "webui.db"
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        owners = connection.execute("SELECT id FROM user WHERE role='admin'").fetchall()
    if len(owners) != 1:
        raise RuntimeError("Expected one existing administrator; select an owner explicitly before installing.")
    owner = owners[0][0]
    installed = []
    for filename in ("functions.json", "tools.json"):
        for entry in json.loads((bundle / filename).read_text(encoding="utf-8")):
            identifier = entry["id"]
            module = types.ModuleType("family_install_" + identifier)
            module.__file__ = str(bundle / (identifier + ".py"))
            sys.modules[module.__name__] = module
            exec(compile(entry["content"], module.__file__, "exec"), module.__dict__)
            entry["meta"]["manifest"] = extract_frontmatter(entry["content"])
            if filename == "functions.json":
                kind, instance = next((kind, getattr(module, name)()) for name, kind in
                    (("Pipe", "pipe"), ("Action", "action"), ("Event", "event")) if hasattr(module, name))
                existing = await Functions.get_function_by_id(identifier)
                if existing and existing.user_id != owner:
                    raise RuntimeError("An existing plugin belongs to another user; installation stopped.")
                if existing is None:
                    await Functions.insert_new_function(owner, kind, FunctionForm(**entry), module=instance)
                elif existing.content != entry["content"]:
                    await Functions.update_function_by_id(identifier, {
                        "content": entry["content"], "name": entry["name"], "meta": entry["meta"],
                    }, user_id=owner, module=instance)
                # Runtime event is global; the manual Action stays scoped to
                # models in review rather than changing the native UI globally.
                await Functions.update_function_by_id(identifier, {
                    "is_active": True, "is_global": kind == "event",
                }, user_id=owner)
            else:
                instance = module.Tools()
                existing = await Tools.get_tool_by_id(identifier)
                if existing and existing.user_id != owner:
                    raise RuntimeError("An existing tool belongs to another user; installation stopped.")
                specs = get_tool_specs(instance)
                if existing is None:
                    await Tools.insert_new_tool(owner, ToolForm(**entry), specs, module=instance)
                elif existing.content != entry["content"]:
                    await Tools.update_tool_by_id(identifier, {
                        "content": entry["content"], "specs": specs,
                        "name": entry["name"], "meta": entry["meta"],
                    }, user_id=owner, module=instance)
            installed.append(identifier)
    model = json.loads((bundle / "family-auto.json").read_text(encoding="utf-8"))
    if await Models.get_model_by_id(model["id"]) is None:
        await Models.insert_new_model(ModelForm(**model), owner)
    print(json.dumps({"installed": installed, "review_model": model["id"], "public_default_changed": False,
                      "provider_requests": 0, "credentials_copied": False}))


if __name__ == "__main__":
    asyncio.run(install(Path(sys.argv[1])))
