"""Check every question in the bank: schema, and that its `verify` expression reproduces `answer`.

Run: python scripts/verify_questions.py [path/to/questions.json]   (exit code 1 on any failure)
"""
import json
import sys
from fractions import Fraction
from itertools import combinations, permutations
from math import factorial, gcd
from pathlib import Path

BANK = Path(__file__).resolve().parent.parent / "src" / "data" / "questions.json"
ENV = {"Fraction": Fraction, "gcd": gcd, "factorial": factorial, "combinations": combinations, "permutations": permutations}
REQUIRED = ["id", "topic", "grade", "difficulty", "type", "stem", "answer", "hints", "solution", "verify"]


def normalize(value):
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(round(value, 6))
    return str(value)


def main():
    bank = Path(sys.argv[1]) if len(sys.argv) > 1 else BANK
    data = json.loads(bank.read_text(encoding="utf-8"))
    topic_ids = {t["id"] for t in data["topics"]}
    seen, errors = set(), []

    for q in data["questions"]:
        qid = q.get("id", "?")
        missing = [k for k in REQUIRED if k not in q]
        if missing:
            errors.append(f"{qid}: missing fields {missing}")
            continue
        if qid in seen:
            errors.append(f"{qid}: duplicate id")
        seen.add(qid)
        if q["topic"] not in topic_ids:
            errors.append(f"{qid}: unknown topic {q['topic']}")
        if q["type"] == "choice" and q["answer"] not in q.get("options", []):
            errors.append(f"{qid}: answer not among options")
        if len(q["hints"]) < 2:
            errors.append(f"{qid}: needs at least 2 hints")
        try:
            got = normalize(eval(q["verify"], dict(ENV)))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{qid}: verify raised {e!r}")
            continue
        if got != q["answer"]:
            errors.append(f"{qid}: verify gives {got}, answer is {q['answer']}")

    total = len(data["questions"])
    if errors:
        print(f"FAILED {len(errors)} / {total}")
        print("\n".join(errors))
        sys.exit(1)
    print(f"OK: all {total} questions verified")


if __name__ == "__main__":
    main()
