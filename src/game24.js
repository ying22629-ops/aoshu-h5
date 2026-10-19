const gcd = (a, b) => (b === 0 ? Math.abs(a) : gcd(b, a % b))

export function frac(n, d = 1) {
  if (d < 0) {
    n = -n
    d = -d
  }
  const g = gcd(n, d) || 1
  return { n: n / g, d: d / g }
}

export const fracLabel = (f) => (f.d === 1 ? String(f.n) : `${f.n}/${f.d}`)
export const is24 = (f) => f.n === 24 && f.d === 1

export const OPS = ['+', '−', '×', '÷']

export function apply(a, op, b) {
  switch (op) {
    case '+':
      return frac(a.n * b.d + b.n * a.d, a.d * b.d)
    case '−':
      return frac(a.n * b.d - b.n * a.d, a.d * b.d)
    case '×':
      return frac(a.n * b.n, a.d * b.d)
    case '÷':
      return b.n === 0 ? null : frac(a.n * b.d, a.d * b.n)
  }
  return null
}

// Steps [{i, j, op}] (indices into the current list, result appended) that reach 24, or null.
// Intermediate results stay non-negative (primary pupils haven't met negatives); fractions only if allowed.
export function solve(values, { allowFrac = true } = {}) {
  if (values.length === 1) return is24(values[0]) ? [] : null
  for (let i = 0; i < values.length; i++) {
    for (let j = 0; j < values.length; j++) {
      if (i === j) continue
      for (const op of OPS) {
        if ((op === '+' || op === '×') && j < i) continue
        const r = apply(values[i], op, values[j])
        if (!r || r.n < 0 || (!allowFrac && r.d !== 1)) continue
        const rest = values.filter((_, k) => k !== i && k !== j)
        const tail = solve([...rest, r], { allowFrac })
        if (tail) return [{ i, j, op }, ...tail]
      }
    }
  }
  return null
}

export const bestSolve = (values) => solve(values, { allowFrac: false }) || solve(values)

export function expression(values, steps) {
  let items = values.map((v) => ({ v, e: fracLabel(v), atom: true }))
  for (const { i, j, op } of steps) {
    const a = items[i]
    const b = items[j]
    const wrap = (x) => (x.atom ? x.e : `(${x.e})`)
    const r = { v: apply(a.v, op, b.v), e: `${wrap(a)} ${op} ${wrap(b)}`, atom: false }
    items = [...items.filter((_, k) => k !== i && k !== j), r]
  }
  return items[0]?.e ?? ''
}

export function newPuzzle(max = 9, rand = Math.random) {
  const allowFrac = max > 9
  for (;;) {
    const nums = Array.from({ length: 4 }, () => 1 + Math.floor(rand() * max))
    if (solve(nums.map((n) => frac(n)), { allowFrac })) return nums
  }
}
