# -*- coding: utf-8 -*-
"""Merge rewritten explanations (_new_m*.jsonl) into quiz-data.json and regenerate quiz-data.js."""
import json
from pathlib import Path

HERE = Path(__file__).parent
data = json.load(open(HERE / "quiz-data.json", encoding="utf-8"))

problems = []
for m in data["modules"]:
    src = HERE / f"_new_m{m['id']}.jsonl"
    if not src.exists():
        problems.append(f"missing {src.name}")
        continue
    new = {}
    for ln, line in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            problems.append(f"{src.name}:{ln} bad json: {e}")
            continue
        new[int(rec["id"])] = rec

    updated = 0
    for q in m["questions"]:
        rec = new.get(int(q["id"]))
        if not rec or not str(rec.get("explain", "")).strip():
            problems.append(f"module {m['id']} q{q['id']}: no new explain")
            continue
        q["explain"] = str(rec["explain"]).strip()
        detail = str(rec.get("detail", "")).strip()
        icon = str(rec.get("icon", "")).strip()
        if detail:
            q["detail"] = detail
        else:
            q.pop("detail", None)
        if icon:
            q["icon"] = icon
        updated += 1
    print(f"module {m['id']}: updated {updated}/{len(m['questions'])}")

if problems:
    print("\nPROBLEMS:")
    for p in problems[:40]:
        print(" -", p)
    print(f"total problems: {len(problems)}")

with open(HERE / "quiz-data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

with open(HERE / "quiz-data.js", "w", encoding="utf-8") as f:
    f.write("window.QUIZ_DATA = ")
    json.dump(data, f, ensure_ascii=False)
    f.write(";\n")

print("\nwrote quiz-data.json and quiz-data.js")
