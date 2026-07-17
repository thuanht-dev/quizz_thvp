# -*- coding: utf-8 -*-
import json
from pathlib import Path

ok = True
for i in range(1, 7):
    rows = [
        json.loads(x)
        for x in Path(f"_new_m{i}.jsonl").read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    src = json.load(open(f"_src_m{i}.json", encoding="utf-8"))
    ids = {r["id"] for r in rows}
    want = {q["id"] for q in src["questions"]}
    bad = []
    if len(rows) != 120:
        bad.append(f"count={len(rows)}")
    if ids != want:
        bad.append(f"missing={want - ids} extra={ids - want}")
    for r in rows:
        if not (
            {"id", "icon", "explain", "detail"} <= set(r)
            and str(r["icon"]).strip()
            and str(r["explain"]).strip()
        ):
            bad.append(f"bad fields id={r.get('id')}")
            break
    empty = sum(not str(r["detail"]).strip() for r in rows)
    icons = len({r["icon"] for r in rows})
    status = "OK" if not bad else "FAIL " + "; ".join(bad)
    print(f"m{i}: {status} | empty detail {empty} | icons {icons}")
    if bad:
        ok = False
print("ALL_OK" if ok else "HAS_ERRORS")
