"""Generate new questions with Claude, then cross-check them before a human ever sees them.

Pipeline for every generated question:
  1. generate  - one Claude call writes the questions (stem, answer, hints, solution, verify)
  2. re-solve  - a second, independent Claude call sees only the stem (and options) and answers it
  3. verify    - the `verify` expression is evaluated with verify_questions.py's ENV + normalize (sandboxed)
  4. triage    - generator answer == re-solved answer == verify result -> scripts/out/pending.json
                 anything else -> scripts/out/rejected.json with the reasons

Usage:
  python scripts/generate_questions.py --topic travel --grade 5 --count 5
  python scripts/generate_questions.py --topic count --grade 4 --count 3 --difficulty 2
  python scripts/generate_questions.py --dry-run          # no API call, built-in fake data, writes to scripts/out/dry-run/

Needs `pip install anthropic` and ANTHROPIC_API_KEY in the environment (not needed for --dry-run).
"""
import argparse
import json
import os
import sys
from datetime import datetime

from qbank import (
    BANK, FIGURE_FIELDS, OUT, answers_equal, check_question, load_json, quiet_console, run_verify, stem_key, write_json,
)

MODEL = "claude-opus-5-5"
MAX_PER_RUN = 10

QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "difficulty": {"type": "integer", "enum": [1, 2, 3]},
        "type": {"type": "string", "enum": ["input", "choice"]},
        "stem": {"type": "string"},
        "options": {"type": "array", "items": {"type": "string"}},
        "answer": {"type": "string"},
        "hints": {"type": "array", "items": {"type": "string"}},
        "solution": {"type": "string"},
        "verify": {"type": "string"},
    },
    "required": ["difficulty", "type", "stem", "options", "answer", "hints", "solution", "verify"],
    "additionalProperties": False,
}
GENERATE_SCHEMA = {
    "type": "object",
    "properties": {"questions": {"type": "array", "items": QUESTION_SCHEMA}},
    "required": ["questions"],
    "additionalProperties": False,
}
SOLVE_SCHEMA = {
    "type": "object",
    "properties": {"reasoning": {"type": "string"}, "answer": {"type": "string"}},
    "required": ["reasoning", "answer"],
    "additionalProperties": False,
}

ANSWER_RULES = """答案格式(与题库判题规则一致):
- 只写最终结果,不带单位,不带“答:”之类的文字。
- 整数直接写,如 12;非整数写成最简分数,如 9/10;负数写 -3。
- 选择题的答案必须与某个选项的文字完全相同。"""

GENERATE_SYSTEM = f"""你是一名小学奥数教研老师,为 1–6 年级学生的思维训练 H5 出题。

出题要求:
- 改编经典题型(换情境、换数据、换问法),绝对不要照搬或轻改杯赛、竞赛真题和教辅原题,题干必须是你自己写的。
- 题目要适合指定年级:只用该年级学过的知识(如一二年级只用 100 以内加减和简单乘法、多用具体情境,三年级不出方程、不出分数运算),数据干净,计算量适中。
- 每道题必须有唯一确定的答案,题意不能有歧义。
- 题目必须只靠文字就能完整理解,不要出需要配图才能做的题(题库里的配图是人工绘制的)。
- hints 至少 2 条,由浅入深,一步一步引导,不要第一条就直接说答案。
- solution 是完整解析,公式用 $...$ 包裹(KaTeX 语法)。
- type 为 "input" 时 options 给空数组;为 "choice" 时给 4 个选项,干扰项要来自常见错误思路。
- verify 是一个独立算出答案的 Python 表达式(单个表达式,不是语句),要按题意直接计算或枚举,
  不要把答案数字直接写进去。可用名字:Fraction、gcd、factorial、combinations、permutations 以及
  sum、range、len、min、max、abs、round、all、any、sorted、set、list 等内置函数。
  表达式结果会被这样规范化后与 answer 做字符串比较:整数值的 float 变成整数;其他 float 保留 6 位小数;
  其余值用 str()。所以非整数答案请让 verify 返回 Fraction(结果 str 为 "9/10"),answer 写 "9/10"。

{ANSWER_RULES}"""

SOLVE_SYSTEM = f"""你是一名严谨的小学奥数老师。请独立、仔细地解出下面这道题,必要时换一种方法验算。
reasoning 里写简要的解题过程,answer 里只写最终答案。

{ANSWER_RULES}"""


# ---------- Claude calls ----------


def make_client():
    try:
        import anthropic
    except ImportError:
        sys.exit("缺少 anthropic SDK:请先运行 pip install anthropic(或使用 --dry-run)")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("未设置环境变量 ANTHROPIC_API_KEY(或使用 --dry-run)")
    return anthropic.Anthropic()


def call_json(client, system, user, schema, model):
    """One structured-output call; returns the parsed JSON object."""
    with client.beta.messages.stream(
        model=model,
        max_tokens=32000,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}},
        # If a safety classifier declines (unlikely for math), let the API retry on a fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"模型拒绝回答: {msg.stop_details}")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("输出被 max_tokens 截断")
    text = next(b.text for b in msg.content if b.type == "text")
    return json.loads(text)


def build_generate_prompt(topic, grade, count, difficulty, bank):
    same_topic = [q for q in bank["questions"] if q["topic"] == topic["id"]]
    examples = [{k: q[k] for k in ("type", "stem", "answer", "hints", "solution", "verify")} for q in same_topic[:2]]
    taken = "\n".join(f"- {q['stem']}" for q in same_topic)
    diff = f"难度统一为 {difficulty}(1 基础 / 2 提高 / 3 挑战)" if difficulty else "难度 1–3 都要有,以 2 为主"
    return f"""请为专题「{topic['name']}」({topic['desc']})出 {count} 道适合 {grade} 年级的题,{diff}。
题型以 input 为主,可以有 1–2 道 choice。

题库里这个专题已有下面这些题,不要重复,也不要只换数字:
{taken or "(暂无)"}

题库中已有题目的风格示例(JSON):
{json.dumps(examples, ensure_ascii=False, indent=2)}"""


def build_solve_prompt(q):
    text = f"题目:{q['stem']}"
    if q["type"] == "choice":
        text += "\n选项:" + " / ".join(q["options"]) + "\n(answer 请填写所选选项的文字)"
    return text


# ---------- dry-run fakes ----------

FAKE_QUESTIONS = [
    {   # good: all three agree
        "difficulty": 1, "type": "input",
        "stem": "【演示】一排路灯从头到尾共 21 盏,相邻两盏相距 5 米。这排路灯首尾相距多少米?",
        "options": [], "answer": "100",
        "hints": ["21 盏灯之间有几个间隔?", "间隔数 = 盏数 − 1。"],
        "solution": "间隔数 $21-1=20$,距离 $20\\times 5=100$(米)。",
        "verify": "(21 - 1) * 5",
    },
    {   # good choice question with a Fraction answer
        "difficulty": 2, "type": "choice",
        "stem": "【演示】计算 $\\dfrac{1}{2\\times3}+\\dfrac{1}{3\\times4}+\\dfrac{1}{4\\times5}$。",
        "options": ["3/10", "1/5", "3/20", "1/2"], "answer": "3/10",
        "hints": ["$\\dfrac{1}{n(n+1)}=\\dfrac1n-\\dfrac1{n+1}$。", "裂项后中间相消,只剩首尾。"],
        "solution": "$\\dfrac12-\\dfrac15=\\dfrac{3}{10}$",
        "verify": "sum(Fraction(1, n * (n + 1)) for n in range(2, 5))",
    },
    {   # rejected: verify disagrees with the stated answer
        "difficulty": 2, "type": "input",
        "stem": "【演示】鸡兔同笼,共 10 个头、28 条腿。兔有几只?",
        "options": [], "answer": "5",
        "hints": ["假设全是鸡,会有多少条腿?", "每把一只鸡换成兔,腿数增加 2。"],
        "solution": "假设全是鸡:$10\\times2=20$ 条腿,少 8 条,兔 $8\\div2=4$ 只。",
        "verify": "(28 - 10 * 2) // (4 - 2)",
    },
    {   # rejected: the independent solver gets a different answer (the stem is ambiguous)
        "difficulty": 2, "type": "input",
        "stem": "【演示】一根绳子对折再对折,然后从中间剪一刀,绳子被剪成几段?",
        "options": [], "answer": "5",
        "hints": ["对折两次后有几层?", "剪一刀会剪断每一层。"],
        "solution": "对折两次共 4 层,剪一刀产生 $4+1=5$ 段。",
        "verify": "2 ** 2 + 1",
    },
    {   # rejected: unsafe verify expression is never executed
        "difficulty": 1, "type": "input",
        "stem": "【演示】$25\\times 4\\times 8$ 等于多少?",
        "options": [], "answer": "800",
        "hints": ["先算 $25\\times4$。", "再乘 8。"],
        "solution": "$25\\times4\\times8=100\\times8=800$",
        "verify": "__import__('os').getcwd() and 800",
    },
]
FAKE_SOLVER_ANSWERS = {  # what the "independent solver" says, keyed by stem
    FAKE_QUESTIONS[0]["stem"]: "100米",
    FAKE_QUESTIONS[1]["stem"]: "3/10",
    FAKE_QUESTIONS[2]["stem"]: "4",
    FAKE_QUESTIONS[3]["stem"]: "9",
    FAKE_QUESTIONS[4]["stem"]: "800",
}


# ---------- pipeline ----------


def triage(q, solved, existing_stems, topic_ids):
    """Return (verify_result, reasons). No reasons means the question goes to pending."""
    reasons = check_question(q, topic_ids)
    if stem_key(q["stem"]) in existing_stems:
        reasons.append("题干与题库或待审核列表中的题重复")
    verify_result, err = run_verify(q["verify"])
    if err:
        reasons.append(err)
    elif verify_result != q["answer"]:
        reasons.append(f"verify 结果 {verify_result} 与 answer {q['answer']} 不一致"
                       "(verify_questions.py 要求字符串完全相同)")
    if solved.get("error"):
        reasons.append(f"独立解题失败: {solved['error']}")
    elif not answers_equal(solved["answer"], q["answer"]):
        reasons.append(f"独立解题得到 {solved['answer']},与 answer {q['answer']} 不一致")
    elif verify_result is not None and not answers_equal(solved["answer"], verify_result):
        reasons.append(f"独立解题得到 {solved['answer']},与 verify 结果 {verify_result} 不一致")
    return verify_result, reasons


def main():
    quiet_console()
    ap = argparse.ArgumentParser(description="用 Claude 生成奥数题并做三方校验")
    ap.add_argument("--topic", help="专题 id,见 questions.json 的 topics(--dry-run 时默认 logic)")
    ap.add_argument("--grade", type=int, choices=[1, 2, 3, 4, 5, 6], help="年级(--dry-run 时默认 4)")
    ap.add_argument("--count", type=int, default=5, help=f"生成数量,1–{MAX_PER_RUN},默认 5")
    ap.add_argument("--difficulty", type=int, choices=[1, 2, 3], help="限定难度,不填则混合")
    ap.add_argument("--model", default=MODEL, help=f"默认 {MODEL}")
    ap.add_argument("--dry-run", action="store_true", help="不调用 API,使用内置假数据,输出到 scripts/out/dry-run/")
    args = ap.parse_args()

    if args.dry_run:
        args.topic = args.topic or "logic"
        args.grade = args.grade or 4
    if not args.topic or not args.grade:
        ap.error("需要 --topic 和 --grade(或使用 --dry-run)")
    if not 1 <= args.count <= MAX_PER_RUN:
        ap.error(f"--count 需要在 1–{MAX_PER_RUN} 之间,要更多请分多次运行")

    bank = load_json(BANK)
    topics = {t["id"]: t for t in bank["topics"]}
    if args.topic not in topics:
        ap.error(f"未知专题 {args.topic},可选:{', '.join(topics)}")
    topic = topics[args.topic]

    out_dir = OUT / "dry-run" if args.dry_run else OUT
    if args.dry_run:  # each dry run starts from a clean slate
        for name in ("pending.json", "rejected.json", "questions.json"):
            (out_dir / name).unlink(missing_ok=True)
    pending_path, rejected_path = out_dir / "pending.json", out_dir / "rejected.json"
    pending = load_json(pending_path, {"questions": []})
    rejected = load_json(rejected_path, {"questions": []})
    existing_stems = {stem_key(q["stem"]) for q in bank["questions"] + pending["questions"]}

    # 1. generate
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    if args.dry_run:
        drafts = [dict(q) for q in FAKE_QUESTIONS[: args.count]]
        print(f"[dry-run] 使用 {len(drafts)} 道内置假题,不调用 API")
        client = None
    else:
        client = make_client()
        print(f"生成中:{topic['name']} / {args.grade} 年级 / {args.count} 道 ({args.model}) ...")
        prompt = build_generate_prompt(topic, args.grade, args.count, args.difficulty, bank)
        drafts = call_json(client, GENERATE_SYSTEM, prompt, GENERATE_SCHEMA, args.model)["questions"]
        print(f"模型返回 {len(drafts)} 道题")

    n_ok = n_bad = 0
    for i, q in enumerate(drafts, 1):
        q = {"topic": args.topic, "grade": args.grade, **q}
        for field in FIGURE_FIELDS:  # figures are hand-drawn, never generated
            q.pop(field, None)
        if q["type"] == "input":
            q.pop("options", None)

        # 2. independent re-solve: the solver sees only the stem (and options), never answer/solution/verify
        if args.dry_run:
            solved = {"answer": FAKE_SOLVER_ANSWERS.get(q["stem"], ""), "reasoning": "(dry-run 假数据)"}
        else:
            try:
                solved = call_json(client, SOLVE_SYSTEM, build_solve_prompt(q), SOLVE_SCHEMA, args.model)
            except Exception as e:  # noqa: BLE001 - one bad call should not lose the whole batch
                solved = {"error": repr(e)}

        # 3. verify + 4. triage
        verify_result, reasons = triage(q, solved, existing_stems, set(topics))
        record = {
            "draft_id": f"{args.topic}-g{args.grade}-{stamp}-{i}",
            **q,
            "_check": {
                "verify_result": verify_result,
                "solver_answer": solved.get("answer"),
                "solver_reasoning": solved.get("reasoning") or solved.get("error"),
                "model": "dry-run" if args.dry_run else args.model,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            },
        }
        label = q["stem"][:30].replace("\n", " ")
        if reasons:
            n_bad += 1
            rejected["questions"].append({**record, "reasons": reasons})
            print(f"  ✗ {record['draft_id']} {label}…\n      " + "\n      ".join(reasons))
        else:
            n_ok += 1
            existing_stems.add(stem_key(q["stem"]))
            pending["questions"].append({**record, "review": "pending", "review_note": ""})
            print(f"  ✓ {record['draft_id']} {label}…  答案 {q['answer']}")

    write_json(pending_path, pending)
    write_json(rejected_path, rejected)
    print(f"\n通过 {n_ok} 道 -> {pending_path}\n拒绝 {n_bad} 道 -> {rejected_path}")
    print("下一步:人工审读 pending.json,把合格题的 review 改为 \"approved\"(不合格改为 \"rejected\" 并写 review_note),"
          "然后运行 python scripts/merge_pending.py" + (" --dry-run" if args.dry_run else ""))


if __name__ == "__main__":
    main()
