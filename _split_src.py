# -*- coding: utf-8 -*-
"""Split quiz-data.json into per-module source files for explanation rewriting."""
import json

d = json.load(open("quiz-data.json", encoding="utf-8"))
for m in d["modules"]:
    out = {
        "id": m["id"],
        "title": m["title"],
        "questions": [
            {
                "id": q["id"],
                "text": q["text"],
                "options": q["options"],
                "answer": q["answer"],
                "old_explain": q["explain"],
            }
            for q in m["questions"]
        ],
    }
    name = f"_src_m{m['id']}.json"
    with open(name, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote", name, len(out["questions"]))
