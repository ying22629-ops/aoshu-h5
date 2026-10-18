"""Shared helpers for the question pipeline: schema checks, sandboxed `verify`, answer comparison, bank I/O.

`verify` is evaluated exactly as scripts/verify_questions.py does it (same ENV, same normalize), but for
model-written expressions it first passes an AST whitelist and then runs in a separate isolated
interpreter with a timeout, so a bad expression can neither touch the machine nor hang the pipeline.
"""
import ast
import json
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
BANK = ROOT / "src" / "data" / "questions.json"
OUT = SCRIPTS / "out"

sys.path.insert(0, str(SCRIPTS))
from verify_questions import ENV, FIGURES, REQUIRED  # noqa: E402

FIELD_ORDER = [
    "id", "topic", "grade", "difficulty", "type", "stem", "figure", "options", "answer", "hints", "solution",
    "solutionFigure", "verify",
]
FIGURE_FIELDS = ("figure", "solutionFigure")  # optional, hand-drawn src/figures/<stem>.svg; never AI-generated
HEAD_FIELDS = FIELD_ORDER[:5]  # written on one line, like the hand-formatted bank

# ---------- verify sandbox ----------

BANNED_NAMES = {
    "eval", "exec", "compile", "open", "input", "breakpoint", "help", "exit", "quit", "globals", "locals",
    "vars", "dir", "getattr", "setattr", "delattr", "hasattr", "type", "object", "memoryview", "bytearray",
    "classmethod", "staticmethod", "property", "super", "print", "id", "hash",
}
ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.Call, ast.keyword, ast.Name, ast.Load,
    ast.Store, ast.Constant, ast.List, ast.Tuple, ast.Set, ast.Dict, ast.Subscript, ast.Slice, ast.IfExp,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.comprehension, ast.Lambda, ast.arguments,
    ast.arg, ast.Starred, ast.Attribute, ast.operator, ast.unaryop, ast.boolop, ast.cmpop,
)
_RUNNER = (
    "import sys, json\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "from verify_questions import ENV, normalize\n"
    "print(json.dumps(normalize(eval(sys.argv[2], dict(ENV)))))\n"
)


def check_expr(expr):
    """Return None if `expr` is an acceptable verify expression, else the reason it is not."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        return f"verify 不是合法的 Python 表达式: {e.msg}"
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            return f"verify 含不允许的语法 {type(node).__name__}"
        if isinstance(node, ast.Name) and (node.id.startswith("_") or node.id in BANNED_NAMES):
            return f"verify 使用了不允许的名字 {node.id}"
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            return f"verify 访问了不允许的属性 {node.attr}"
    return None


def run_verify(expr, timeout=5):
    """Evaluate `expr` with verify_questions' ENV + normalize. Returns (value, error); exactly one is None."""
    reason = check_expr(expr)
    if reason:
        return None, reason
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", _RUNNER, str(SCRIPTS), expr],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, f"verify 运行超过 {timeout} 秒"
    if proc.returncode != 0:
        last = (proc.stderr.strip().splitlines() or ["unknown error"])[-1]
        return None, f"verify 运行出错: {last}"
    return json.loads(proc.stdout), None


# ---------- answers ----------

_FULLWIDTH = re.compile(r"[！-～]")
_UNIT_TAIL = re.compile(r"[一-龥°]+$")


def canon_answer(raw):
    """Same normalisation the front end applies to typed answers (src/bank.js normalizeAnswer)."""
    s = _FULLWIDTH.sub(lambda m: chr(ord(m.group()) - 0xFEE0), str(raw))
    s = re.sub(r"\s+", "", s.replace("÷", "/"))
    return _UNIT_TAIL.sub("", s)


def answers_equal(a, b):
    """Equal as the front end would judge them: same string, or same number (9/10 == 0.9)."""
    a, b = canon_answer(a), canon_answer(b)
    if a == b:
        return True
    try:
        return Fraction(a) == Fraction(b)
    except (ValueError, ZeroDivisionError):
        return False


# ---------- schema ----------


def check_question(q, topic_ids):
    """Schema problems for one question (without requiring `id`). Empty list means OK."""
    errors = [f"缺少字段 {k}" for k in REQUIRED if k != "id" and k not in q]
    if errors:
        return errors
    if q["topic"] not in topic_ids:
        errors.append(f"未知专题 {q['topic']}")
    if q["grade"] not in range(1, 7):
        errors.append(f"年级 {q['grade']} 不在 1–6")
    if q["difficulty"] not in (1, 2, 3):
        errors.append(f"难度 {q['difficulty']} 不在 1–3")
    if q["type"] not in ("input", "choice"):
        errors.append(f"题型 {q['type']} 不是 input/choice")
    for k in ("stem", "answer", "solution", "verify"):
        if not isinstance(q[k], str) or not q[k].strip():
            errors.append(f"{k} 为空")
    if not isinstance(q["hints"], list) or len(q["hints"]) < 2:
        errors.append("提示少于 2 条")
    for field in FIGURE_FIELDS:
        if field in q and not (FIGURES / f"{q[field]}.svg").is_file():
            errors.append(f"{field} 引用的 src/figures/{q[field]}.svg 不存在")
    if q["type"] == "choice":
        opts = q.get("options") or []
        if len(opts) < 2 or len(set(opts)) != len(opts):
            errors.append("选择题需要至少 2 个互不相同的选项")
        elif q["answer"] not in opts:
            errors.append("答案不在选项中")
    return errors


def stem_key(stem):
    return re.sub(r"\s+", "", stem)


# ---------- bank I/O ----------


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _j(v):
    return json.dumps(v, ensure_ascii=False)


def format_question(q):
    """One question block in the same hand-formatted layout as src/data/questions.json."""
    head = ", ".join(f"{_j(k)}: {_j(q[k])}" for k in HEAD_FIELDS if k in q)
    rows = [head] + [f"{_j(k)}: {_j(q[k])}" for k in FIELD_ORDER[5:] if k in q]
    rows += [f"{_j(k)}: {_j(v)}" for k, v in q.items() if k not in FIELD_ORDER]
    return "    {\n" + ",\n".join("      " + r for r in rows) + "\n    }"


def append_questions(raw, questions):
    """Splice new question blocks onto the end of the bank text, leaving every existing byte untouched."""
    tail = re.search(r"\n  \]\s*\}\s*$", raw)
    if not tail:
        raise ValueError("questions.json 结尾不是预期的 '  ]\\n}' 格式,无法安全追加")
    blocks = ",\n".join(format_question(q) for q in questions)
    new = raw[: tail.start()] + ",\n" + blocks + raw[tail.start():]
    expected = json.loads(raw)
    expected["questions"] += questions
    if json.loads(new) != expected:
        raise ValueError("追加后的 questions.json 与预期内容不一致")
    return new


def quiet_console():
    """Windows consoles default to GBK; never crash on a character it cannot show."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

