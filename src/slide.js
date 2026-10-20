export const solved = (n) => [...Array.from({ length: n * n - 1 }, (_, i) => i + 1), 0]

export const isSolved = (tiles) => tiles.every((v, i) => v === (i === tiles.length - 1 ? 0 : i + 1))

function neighbors(n, i) {
  const r = Math.floor(i / n)
  const c = i % n
  const out = []
  if (r > 0) out.push(i - n)
  if (r < n - 1) out.push(i + n)
  if (c > 0) out.push(i - 1)
  if (c < n - 1) out.push(i + 1)
  return out
}

// A random walk of the blank from the solved state, so every puzzle is solvable.
export function scramble(n, steps, rand = Math.random) {
  for (;;) {
    const t = solved(n)
    let blank = t.length - 1
    let prev = -1
    for (let s = 0; s < steps; s++) {
      const options = neighbors(n, blank).filter((x) => x !== prev)
      const next = options[Math.floor(rand() * options.length)]
      ;[t[blank], t[next]] = [t[next], t[blank]]
      prev = blank
      blank = next
    }
    if (!isSolved(t)) return t
  }
}

// Slides every tile between `idx` and the blank one step toward it; returns { tiles, moved } or null.
export function slideFrom(tiles, n, idx) {
  const blank = tiles.indexOf(0)
  const [br, bc] = [Math.floor(blank / n), blank % n]
  const [r, c] = [Math.floor(idx / n), idx % n]
  if (idx === blank || (r !== br && c !== bc)) return null
  const dir = r === br ? (c < bc ? -1 : 1) : r < br ? -n : n
  const t = [...tiles]
  let cur = blank
  let moved = 0
  while (cur !== idx) {
    const nxt = cur + dir
    t[cur] = t[nxt]
    t[nxt] = 0
    cur = nxt
    moved++
  }
  return { tiles: t, moved }
}
