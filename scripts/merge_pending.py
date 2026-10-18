"""Merge human-approved questions from scripts/out/pending.json into src/data/questions.json.

Review workflow: open pending.json, read each question, then set
  "review": "approved"   -> merged into the bank by this script
  "review": "rejected"   -> moved to rejected.json (put the reason in "review_note")
  "review": "pending"    -> left alone for later
You may edit stem / answer / hints / solution / verify while reviewing; everything is re-checked here.

This script assigns ids (topic-NN, continuing each topic's numbering), re-checks schema and `verify`,
appends the questions to the bank without touching existing text, and runs scripts/verify_questions.py
on the result. If anything fails, the bank is left unchanged.

Usage:
  python scripts/merge_pending.py
  python scripts/merge_pending.py --dry-run   # treats every pending item in scripts/out/dry-run/ as approved and
                                              # writes scripts/out/dry-run/questions.json; the real bank is not touched
"""
import argparse
import os
import re
import subprocess
import sys

from qbank import (
    BANK, OUT, SCRIPTS, append_questions, check_question, load_json, quiet_console, run_verify, stem_key, write_json,
)

META_KEYS = ("draft_id", "review", "review_note", "_check", "reasons")


def next_ids(bank_questions, new_questions):
    """Give each new question the next free `topic-NN` id."""
    last = {}
    for q in bank_questions:
        m = re.fullmatch(r"(.+)-(\d+)", q["id"])
        if m:
            last[m.group(1)] = max(last.get(m.group(1), 0), int(m.group(2)))
    for q in new_questions:
        n = last.get(q["topic"], 0) + 1
        last[q["topic"]] = n
        q["id"] = f"{q['topic']}-{n:02d}"


def main():
    quiet_console()
    ap = argparse.ArgumentParser(description="把审核通过的题合并进题库")
    ap.add_argument("--dry-run", action="store_true",
                    help="演示模式:读 scripts/out/dry-run/pending.json,全部视为通过,写到 scripts/out/dry-run/questions.json")
    args = ap.parse_args()

    out_dir = OUT / "dry-run" if args.dry_run else OUT
    pending_path, rejected_path = out_dir / "pending.json", out_dir / "rejected.json"
    target = out_dir / "questions.json" if args.dry_run else BANK

    pending = load_json(pending_path)
    if not pending or not pending["questions"]:
        sys.exit(f"{pending_path} 里没有待审核的题")
    if args.dry_run:
        print("[dry-run] 把所有 review=pending 的题视为人工审核通过")
        for item in pending["questions"]:
            if item.get("review") == "pending":
                item["review"] = "approved"

    approved = [x for x in pending["questions"] if x.get("review") == "approved"]
    refused = [x for x in pending["questions"] if x.get("review") == "rejected"]
    waiting = [x for x in pending["questions"] if x.get("review") not in ("approved", "rejected")]
    if not approved and not refused:
        print(f"没有 review 为 approved 或 rejected 的题({len(waiting)} 道仍待审核),无事可做")
        return

    raw = BANK.read_text(encoding="utf-8")
    bank = load_json(BANK)
    topic_ids = {t["id"] for t in bank["topics"]}
    seen = {stem_key(q["stem"]) for q in bank["questions"]}

    # Re-check everything: the reviewer may have edited the question.
    new_questions, errors = [], []
    for item in approved:
        q = {k: v for k, v in item.items() if k not in META_KEYS}
        if q.get("type") == "input":
            q.pop("options", None)
        problems = check_question(q, topic_ids)
        if not problems:
            got, err = run_verify(q["verify"])
            if err:
                problems.append(err)
            elif got != q["answer"]:
                problems.append(f"verify 结果 {got} 与 answer {q['answer']} 不一致")
            if stem_key(q["stem"]) in seen:
                problems.append("题干与题库中已有的题重复")
            seen.add(stem_key(q["stem"]))
        if problems:
            errors.append(f"{item.get('draft_id', '?')}: " + ";".join(problems))
        new_questions.append(q)
    if errors:
        print("以下已通过审核的题没有通过复查,本次未合并任何题,请修改 pending.json 后重试:")
        print("\n".join("  " + e for e in errors))
        sys.exit(1)

    if new_questions:
        next_ids(bank["questions"], new_questions)
        # `id` first, then the usual field order (append_questions formats the rest).
        new_questions = [{"id": q["id"], **{k: v for k, v in q.items() if k != "id"}} for q in new_questions]
        tmp = target.with_name(target.name + ".tmp")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(append_questions(raw, new_questions), encoding="utf-8", newline="\n")
        check = subprocess.run([sys.executable, str(SCRIPTS / "verify_questions.py"), str(tmp)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(check.stdout.strip())
        if check.returncode != 0:
            tmp.unlink()
            sys.exit(f"合并后的题库没有通过 verify_questions.py,{target} 未改动")
        os.replace(tmp, target)
        for q in new_questions:
            print(f"  + {q['id']}  {q['stem'][:30]}…")

    rejected = load_json(rejected_path, {"questions": []})
    for item in refused:
        rejected["questions"].append({**item, "reasons": [f"人工审核未通过: {item.get('review_note') or '未注明'}"]})
    pending["questions"] = waiting
    write_json(rejected_path, rejected)
    write_json(pending_path, pending)

    print(f"\n合并 {len(new_questions)} 道 -> {target}")
    print(f"人工拒绝 {len(refused)} 道 -> {rejected_path};仍待审核 {len(waiting)} 道")
    if not args.dry_run and new_questions:
        print("记得重新打包:npm run build")


if __name__ == "__main__":
    main()
