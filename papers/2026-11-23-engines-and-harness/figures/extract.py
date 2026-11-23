"""Tabulate bench result JSON files (read-only). Usage: extract.py <results dir>"""
import json, sys, glob, os

root = sys.argv[1]
KEYS = ["gyro-l-2026-11-22", "signal-2-2026-11-23", "signal-2-dual-a", "signal-2-dual-b",
        "signal-2-dual-a-hardredo", "inkling-locals-2026-11-22", "inkling-mtplx-2026-11-22",
        "inkling-mtplx-think-redo", "inkling-mtplx-low", "inkling-mtplx-medium", "inkling-mtplx-off",
        "inkling-strata-sq20", "inkling-strata-sq20-fix", "inkling-strata-sq20-fix2",
        "inkling-mtplx-low-rules", "inkling-mtplx-low-rules2", "inkling-mtplx2132-low-rules",
        "inkling-locals-loopnote"]
out = {}
for s in ["short", "easy", "hard", "real"]:
    for k in KEYS:
        for f in sorted(glob.glob(f"{root}/{s}/{k}/rep*.json")):
            d = json.load(open(f))
            rep = os.path.basename(f)[:-5]
            row = {kk: d.get(kk) for kk in ["passed", "n", "wall_s", "status", "output_tokens", "tok_per_s"]}
            if s == "real":
                row["tasks"] = {t["task"]: [t["ok"], t["wall_s"]] for t in d["tasks"]}
            out[f"{s}/{k}/{rep}"] = row
            print(s, k, rep, row)
json.dump(out, open(sys.argv[2], "w"), indent=1)
