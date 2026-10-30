"""Build standalone notebooks from the readable, versioned delivery source package.

This command assembles files only. It does not train models, read competition
data or reuse outputs from any previous notebook execution.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(week: int) -> Path:
    """Embed the pinned sources in a clean, output-free notebook template."""
    manifest = json.loads((ROOT / "src/runtime/manifest.json").read_text(encoding="utf-8"))
    entry = manifest["weeks"][str(week)]
    notebook = json.loads((ROOT / entry["template"]).read_text(encoding="utf-8"))
    sources = {}
    for item in entry["sources"]:
        text = (ROOT / item["file"]).read_text(encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest != item["sha256"]:
            raise ValueError(f"Source fingerprint changed; review the manifest first: {item['file']}")
        compile(text, item["key"], "exec")
        sources[item["key"]] = text
    embedded = []
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        text = "".join(cell["source"])
        if text.startswith("SOURCES["):
            statement = ast.parse(text).body[0]
            key = ast.literal_eval(statement.targets[0].slice)
            cell["source"] = [f"SOURCES[{key!r}] = {sources[key]!r}\n"]
            embedded.append(key)
        elif text.startswith("DATAFILES = "):
            datafiles = ast.literal_eval(ast.parse(text).body[0].value)
            source_record = json.loads(datafiles["receta/codigo.json"])
            source_record["files"] = {
                key: {"sha256": hashlib.sha256(value.encode("utf-8")).hexdigest()}
                for key, value in sources.items()
            }
            datafiles["receta/codigo.json"] = json.dumps(source_record, ensure_ascii=False, indent=2) + "\n"
            cell["source"] = [f"DATAFILES = {datafiles!r}\n"]
        compile("".join(cell["source"]), "<notebook cell>", "exec")
        cell["execution_count"] = None
        cell["outputs"] = []
    if set(embedded) != set(sources) or len(embedded) != entry["source_count"]:
        raise ValueError("The notebook source cells do not match the delivery manifest")
    output = ROOT / entry["notebook"]
    output.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", choices=("1", "2", "both"), default="both")
    args = parser.parse_args()
    for selected in ((1, 2) if args.week == "both" else (int(args.week),)):
        print(build(selected))
