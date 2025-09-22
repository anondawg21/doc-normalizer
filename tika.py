#!/usr/bin/env python3
# Send files in tika_samples/ to your running Tika server and save results.

import os, json, pathlib, sys, subprocess
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

TIKA_URL = os.environ.get("TIKA_URL", "http://127.0.0.1:9998")  # change if needed
SRC = pathlib.Path("tika_samples")
OUT = pathlib.Path("tika_output")
for d in ("text", "meta", "rmeta"): (OUT/d).mkdir(parents=True, exist_ok=True)

s = requests.Session()
TIMEOUT = 120

def put(endpoint, file_path, accept):
    with open(file_path, "rb") as f:
        r = s.put(f"{TIKA_URL}{endpoint}", data=f, headers={"Accept": accept}, timeout=TIMEOUT)
    r.raise_for_status()
    return r

detect_rows, lang_rows = [], []

for fp in sorted(SRC.glob("*")):
    if fp.is_dir(): continue
    # plain text
    r = put("/tika", fp, "text/plain")
    (OUT/"text"/(fp.name + ".txt")).write_text(r.text, encoding="utf-8")

    # metadata (simple)
    r = put("/meta", fp, "application/json")
    try:
        (OUT/"meta"/(fp.stem + ".json")).write_text(
            json.dumps(r.json(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        (OUT/"meta"/(fp.stem + ".json")).write_text(r.text, encoding="utf-8")

    # recursive metadata (includes embedded items)
    r = put("/rmeta/json", fp, "application/json")
    try:
        (OUT/"rmeta"/(fp.stem + ".json")).write_text(
            json.dumps(r.json(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        (OUT/"rmeta"/(fp.stem + ".json")).write_text(r.text, encoding="utf-8")

    # media type + language
    detect_rows.append(f"{fp.name}\t{put('/detect/stream', fp, 'text/plain').text.strip()}")
    lang_rows.append(f"{fp.name}\t{put('/language/stream', fp, 'text/plain').text.strip()}")

(OUT/"detected_mime.tsv").write_text("\n".join(detect_rows), encoding="utf-8")
(OUT/"detected_language.tsv").write_text("\n".join(lang_rows), encoding="utf-8")
print(f"Done -> {OUT.resolve()}")
