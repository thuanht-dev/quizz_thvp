# -*- coding: utf-8 -*-
"""Find and rewrite weak quiz explains."""
import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\thuanht\Downloads\Thi THVP\quiz")
JSON_PATH = ROOT / "quiz-data.json"
JS_PATH = ROOT / "quiz-data.js"

BAD_PHRASES = [
    "khớp với kiến thức chuẩn",
    "các lựa chọn khác không chính xác",
    "Hãy nắm đặc điểm cốt lõi",
    "trong cùng chủ đề",
    "định nghĩa này để phân biệt",
]

FILLER_SUFFIX = (
    "Hãy nắm đặc điểm cốt lõi trong định nghĩa này để phân biệt "
    "với các khái niệm gần nghĩa trong cùng chủ đề."
)

# Manual rewrites keyed by (module_key, question_id)
# module_key is the JSON key under modules or similar — we'll discover structure


def find_bad(explain: str) -> bool:
    return any(p in explain for p in BAD_PHRASES)


def main():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print("TOP:", type(data).__name__, list(data.keys()) if isinstance(data, dict) else "n/a")

    # Discover structure and collect bad items
    bad_items = []

    def walk_modules(obj):
        # Try common shapes
        if isinstance(obj, dict):
            if "modules" in obj:
                return obj["modules"]
            # maybe modules are top-level Module1 etc
            mods = []
            for k, v in obj.items():
                if isinstance(v, dict) and "questions" in v:
                    mods.append((k, v))
                elif isinstance(v, list) and v and isinstance(v[0], dict) and "text" in v[0]:
                    mods.append((k, {"questions": v}))
            if mods:
                return mods
        return None

    modules = None
    if isinstance(data, dict):
        if "modules" in data:
            m = data["modules"]
            if isinstance(m, list):
                modules = []
                for i, mod in enumerate(m):
                    name = mod.get("name") or mod.get("title") or mod.get("id") or f"module_{i}"
                    modules.append((str(name), mod))
            elif isinstance(m, dict):
                modules = list(m.items())
        else:
            # keys like module1 / Module 1
            modules = []
            for k, v in data.items():
                if isinstance(v, dict) and ("questions" in v or "items" in v):
                    modules.append((k, v))
                elif isinstance(v, list) and v and isinstance(v[0], dict) and ("text" in v[0] or "question" in v[0]):
                    modules.append((k, {"questions": v}))

    print("MODULES found:", len(modules) if modules else 0)
    if modules:
        for name, mod in modules[:3]:
            qs = mod.get("questions") or mod.get("items") or []
            print(f"  {name}: {len(qs)} questions, sample keys {list(qs[0].keys()) if qs else None}")

    # Also dump Module1 Q26 and Module4 Q48
    def get_q(mod_idx_or_name, qid):
        for name, mod in modules:
            qs = mod.get("questions") or mod.get("items") or []
            for q in qs:
                if q.get("id") == qid:
                    # check if this is the right module by name/index
                    yield name, q

    print("\n=== ALL Q26 ===")
    for name, q in get_q(None, 26):
        print(name, q.get("text", "")[:80], "|", q.get("answer"), "|", q.get("explain", "")[:120])

    print("\n=== ALL Q48 ===")
    for name, q in get_q(None, 48):
        print(name, q.get("text", "")[:80], "|", q.get("answer"), "|", q.get("explain", "")[:120])

    print("\n=== BAD EXPLAINS ===")
    count = 0
    for name, mod in modules:
        qs = mod.get("questions") or mod.get("items") or []
        for q in qs:
            ex = q.get("explain") or ""
            if find_bad(ex):
                count += 1
                ans = q.get("answer")
                opt = (q.get("options") or {}).get(ans, "")
                print(f"--- [{name}] Q{q.get('id')} ---")
                print(f"Q: {q.get('text')}")
                print(f"A({ans}): {opt}")
                print(f"OLD: {ex}")
                print()
    print(f"TOTAL BAD: {count}")


if __name__ == "__main__":
    main()
