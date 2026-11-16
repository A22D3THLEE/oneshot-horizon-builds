"""Refreshes catalog/maps.json from the official CurseForge API.

For each map with a curseforge.com/minecraft/worlds/<slug> page it updates the picture
(a link to CurseForge's CDN, nothing is re-hosted), the author, the game versions, the
download count and whether the author lets other apps hand the file out. The name and
the Russian note written by hand are kept.

Our API key may not use /mods/search, so a map is found by its project id (cf_id).
A new map without cf_id gets it once from the public api.cfwidget.com lookup.

Needs env CURSEFORGE_API_KEY. Usage: py -I tools/update_maps.py catalog/maps.json
"""
import json, os, re, sys, time, urllib.request

API = "https://api.curseforge.com/v1"
UA = "oneshot-catalog"


def call(path, key, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(API + path, data=data, headers={
        "x-api-key": key, "Accept": "application/json", "Content-Type": "application/json",
        "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def lookup_id(slug):
    req = urllib.request.Request("https://api.cfwidget.com/minecraft/worlds/" + slug,
                                 headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return int(json.load(r)["id"])
    except Exception as e:
        print("no id for", slug, "-", e)
        return None


def vkey(v):
    return tuple(int(p) for p in v.split("."))


def versions(mod):
    vs = {i.get("gameVersion", "") for i in mod.get("latestFilesIndexes", [])}
    vs = sorted((v for v in vs if re.fullmatch(r"\d+(\.\d+)+", v)), key=vkey)
    if not vs:
        return None
    return vs[0] if len(vs) == 1 else vs[0] + "–" + vs[-1]


def picture(mod):
    for s in mod.get("screenshots") or []:
        if s.get("url"):
            return s["url"]
    logo = mod.get("logo") or {}
    return logo.get("url") or logo.get("thumbnailUrl")


def main():
    path = sys.argv[1]
    key = os.environ.get("CURSEFORGE_API_KEY", "").strip()
    if not key:
        sys.exit("CURSEFORGE_API_KEY is not set")
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    for m in doc["maps"]:
        hit = re.search(r"curseforge\.com/minecraft/worlds/([^/?#]+)", m.get("page", ""))
        if hit and not m.get("cf_id"):
            cid = lookup_id(hit.group(1))
            if cid:
                m["cf_id"] = cid
            time.sleep(1)
    ids = [m["cf_id"] for m in doc["maps"] if m.get("cf_id")]
    mods = {d["id"]: d for d in call("/mods", key, {"modIds": ids}).get("data", [])} if ids else {}
    found = 0
    for m in doc["maps"]:
        mod = mods.get(m.get("cf_id"))
        if not mod:
            continue
        found += 1
        img = picture(mod)
        if img:
            m["image"] = img
        if mod.get("authors"):
            m["author"] = mod["authors"][0].get("name", m.get("author"))
        v = versions(mod)
        if v:
            m["versions"] = v
        m["downloads"] = int(mod.get("downloadCount") or 0)
        m["updated"] = (mod.get("dateModified") or "")[:10]
        m["distributable"] = bool(mod.get("allowModDistribution"))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write('{"maps": [\n')
        f.write(",\n".join("  " + json.dumps(m, ensure_ascii=False) for m in doc["maps"]))
        f.write("\n]}\n")
    print("updated", found, "of", len(doc["maps"]), "maps")


if __name__ == "__main__":
    main()
