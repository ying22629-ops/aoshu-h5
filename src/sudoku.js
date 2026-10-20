export const CONFIGS = {
  4: { n: 4, br: 2, bc: 2, holes: 10 },
  6: { n: 6, br: 2, bc: 3, holes: 20 },
}

const shuffle = (arr, rand) => {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}
const range = (n) => Array.from({ length: n }, (_, i) => i)

export function boxOf(cfg, r, c) {
  return Math.floor(r / cfg.br) * (cfg.n / cfg.bc) + Math.floor(c / cfg.bc)
}

export function isValidGrid(cfg, g) {
  const { n } = cfg
  const full = (vals) => new Set(vals).size === n && vals.every((v) => v >= 1 && v <= n)
  for (let i = 0; i < n; i++) {
    if (!full(g[i])) return false
    if (!full(g.map((row) => row[i]))) return false
  }
  for (let b = 0; b < n; b++) {
    const vals = []
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (boxOf(cfg, r, c) === b) vals.push(g[r][c])
    if (!full(vals)) return false
  }
  return true
}

function solvedGrid(cfg, rand) {
  const { n, br, bc } = cfg
  const digits = shuffle(range(n), rand)
  const bands = shuffle(range(n / br), rand)
  const rows = bands.flatMap((b) => shuffle(range(br), rand).map((r) => b * br + r))
  const stacks = shuffle(range(n / bc), rand)
  const cols = stacks.flatMap((s) => shuffle(range(bc), rand).map((c) => s * bc + c))
  return rows.map((r) => cols.map((c) => digits[(bc * (r % br) + Math.floor(r / br) + c) % n] + 1))
}

export function countSolutions(cfg, grid, limit = 2) {
  const { n } = cfg
  const g = grid.map((row) => [...row])
  let count = 0
  const ok = (r, c, v) => {
    for (let i = 0; i < n; i++) if (g[r][i] === v || g[i][c] === v) return false
    const b = boxOf(cfg, r, c)
    for (let rr = 0; rr < n; rr++)
      for (let cc = 0; cc < n; cc++) if (g[rr][cc] === v && boxOf(cfg, rr, cc) === b) return false
    return true
  }
  const walk = (pos) => {
    if (count >= limit) return
    if (pos === n * n) {
      count++
      return
    }
    const r = Math.floor(pos / n)
    const c = pos % n
    if (g[r][c]) return walk(pos + 1)
    for (let v = 1; v <= n; v++) {
      if (!ok(r, c, v)) continue
      g[r][c] = v
      walk(pos + 1)
      g[r][c] = 0
    }
  }
  walk(0)
  return count
}

export function newSudoku(size = 4, rand = Math.random) {
  const cfg = CONFIGS[size]
  const solution = solvedGrid(cfg, rand)
  const puzzle = solution.map((row) => [...row])
  let holes = 0
  for (const pos of shuffle(range(cfg.n * cfg.n), rand)) {
    if (holes >= cfg.holes) break
    const r = Math.floor(pos / cfg.n)
    const c = pos % cfg.n
    const keep = puzzle[r][c]
    puzzle[r][c] = 0
    if (countSolutions(cfg, puzzle) === 1) holes++
    else puzzle[r][c] = keep
  }
  return { cfg, solution, puzzle }
}
