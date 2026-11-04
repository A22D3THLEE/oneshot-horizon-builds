"""Native mods for the "OneShot + mods" build, from Horizon's mod registry (reviewed mods only).

    python pick_mods.py INDEX.json MODS.txt HOOKS_API COMMIT OUT_DIR

For each id in MODS.txt (one per line, # comments): the newest version made for Minecraft 26.3, downloaded from the
registry's own address and checked against its SHA-256, unpacked to OUT_DIR/<id>/ (the bundle: horizon-mixin.toml and
its helpers). A mod that needs newer native hook points than this Horizon has (HOOKS_API) or that pins another
Horizon commit is left out. Each bundle is told it builds on COMMIT, as the official launcher does in its copy.
Prints one line per mod taken: "<id> <version> <horizon-mixins commit>".
"""
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile

GAME = "26.3"


def main():
    index_path, list_path, hooks_api, commit, out = sys.argv[1:6]
    hooks_api = int(hooks_api)
    index = json.load(open(index_path, encoding="utf-8"))
    revoked = {(r.get("sha256") or "").lower() for r in index.get("revoked", [])}
    projects = {p.get("id"): p for p in index.get("projects", [])}
    wanted = [l.split("#")[0].strip() for l in open(list_path, encoding="utf-8")]
    for mod_id in [w for w in wanted if w]:
        project = projects.get(mod_id)
        if not project or project.get("kind") != "native-mod":
            print(f"::warning::{mod_id}: not a native mod in the registry", file=sys.stderr)
            continue
        version = next((v for v in project.get("versions", []) if v.get("game") == GAME), None)
        if not version:
            print(f"::warning::{mod_id}: no version for {GAME}", file=sys.stderr)
            continue
        file = version["file"]
        sha = (file.get("sha256") or "").lower()
        if len(sha) != 64 or sha in revoked:
            print(f"::warning::{mod_id}: revoked or without a checksum", file=sys.stderr)
            continue
        data = urllib.request.urlopen(file["url"], timeout=60).read()
        if hashlib.sha256(data).hexdigest() != sha:
            print(f"::warning::{mod_id}: the download does not match its checksum", file=sys.stderr)
            continue
        bundle = zipfile.ZipFile(io.BytesIO(data))
        meta = json.loads(bundle.read("horizon-native.json"))
        hooks = meta.get("hooks")
        if hooks is None:
            # Pinned to one Horizon commit: only that one is sure to build.
            if meta.get("horizon") != commit:
                print(f"::warning::{mod_id}: pinned to Horizon {meta.get('horizon', '?')[:7]}", file=sys.stderr)
                continue
        elif int(hooks) > hooks_api:
            print(f"::warning::{mod_id}: needs native hooks {hooks}, this Horizon has {hooks_api}", file=sys.stderr)
            continue
        prefix = f"mixins/{mod_id}/"
        names = [n for n in bundle.namelist() if n.startswith(prefix) and not n.endswith("/")]
        if not any(n == prefix + "horizon-mixin.toml" for n in names):
            print(f"::warning::{mod_id}: no horizon-mixin.toml", file=sys.stderr)
            continue
        for name in names:
            rel = name[len(prefix):]
            if rel.startswith("/") or ".." in rel.split("/"):
                continue
            target = f"{out}/{mod_id}/{rel}"
            import os
            os.makedirs(os.path.dirname(target), exist_ok=True)
            content = bundle.read(name)
            if rel == "horizon-mixin.toml":
                text = content.decode("utf-8")
                text = re.sub(r'(?m)^horizon_revision\s*=.*$', f'horizon_revision = "{commit}"', text)
                content = text.encode("utf-8")
            open(target, "wb").write(content)
        print(f"{mod_id} {version['version']} {meta.get('mixins', '')}")


if __name__ == "__main__":
    main()
