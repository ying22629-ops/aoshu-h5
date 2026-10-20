<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { boxOf, newSudoku } from '../sudoku.js'
import { state } from '../store.js'
import { GAME_STARS } from '../rewards.js'
import { sfx } from '../sfx.js'
import { confetti } from '../confetti.js'

const MAX_HINTS = 2
const router = useRouter()
const game = ref(null)
const board = ref([])
const sel = ref(null)
const hints = ref(0)
const won = ref(false)
const msg = ref('')

const size = computed(() => (state.sudoku.hard ? 6 : 4))
const cfg = computed(() => game.value.cfg)

function fresh() {
  game.value = newSudoku(size.value)
  board.value = game.value.puzzle.map((row) => [...row])
  sel.value = null
  hints.value = 0
  won.value = false
  msg.value = ''
}
fresh()

const given = (r, c) => game.value.puzzle[r][c] !== 0

const conflicts = computed(() => {
  const { n } = cfg.value
  const bad = new Set()
  const cells = []
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (board.value[r][c]) cells.push([r, c])
  for (const [r, c] of cells)
    for (const [r2, c2] of cells) {
      if (r === r2 && c === c2) continue
      if (board.value[r][c] !== board.value[r2][c2]) continue
      if (r === r2 || c === c2 || boxOf(cfg.value, r, c) === boxOf(cfg.value, r2, c2)) bad.add(`${r},${c}`)
    }
  return bad
})

const filled = computed(() => board.value.every((row) => row.every(Boolean)))

function cellClass(r, c) {
  const s = sel.value
  const v = board.value[r][c]
  const n = cfg.value.n
  return {
    given: given(r, c),
    sel: s && s.r === r && s.c === c,
    peer: s && (s.r === r || s.c === c || boxOf(cfg.value, s.r, s.c) === boxOf(cfg.value, r, c)),
    same: s && v && board.value[s.r][s.c] === v,
    bad: conflicts.value.has(`${r},${c}`),
    br: (c + 1) % cfg.value.bc === 0 && c < n - 1,
    bb: (r + 1) % cfg.value.br === 0 && r < n - 1,
  }
}

function pick(r, c) {
  if (won.value) return
  sel.value = { r, c }
  sfx.tap()
}

function put(v) {
  const s = sel.value
  if (won.value) return
  if (!s) return (msg.value = '先点一个空格子')
  if (given(s.r, s.c)) return (msg.value = '这个数字是题目给的,不能改哦')
  board.value[s.r][s.c] = v
  msg.value = ''
  sfx.tap()
  check()
}

function check() {
  if (!filled.value || conflicts.value.size) return
  won.value = true
  state.sudoku.wins += 1
  msg.value = `完成啦!获得 ${GAME_STARS.sudoku} 颗星 ⭐`
  sfx.win()
  confetti(48)
}

function hint() {
  if (won.value || hints.value >= MAX_HINTS) return
  const { n } = cfg.value
  let target = sel.value && !given(sel.value.r, sel.value.c) && board.value[sel.value.r][sel.value.c] !== game.value.solution[sel.value.r][sel.value.c] ? sel.value : null
  if (!target) {
    for (let r = 0; r < n && !target; r++)
      for (let c = 0; c < n && !target; c++)
        if (board.value[r][c] !== game.value.solution[r][c]) target = { r, c }
  }
  if (!target) return
  hints.value += 1
  board.value[target.r][target.c] = game.value.solution[target.r][target.c]
  sel.value = target
  msg.value = `提示:这一格是 ${game.value.solution[target.r][target.c]}`
  check()
}

function clearAll() {
  board.value = game.value.puzzle.map((row) => [...row])
  msg.value = ''
}

function setHard(v) {
  if (!!state.sudoku.hard === v) return
  state.sudoku.hard = v
  fresh()
}

function onKey(e) {
  if (e.metaKey || e.ctrlKey || e.altKey) return
  const n = cfg.value.n
  const d = Number(e.key)
  if (d >= 1 && d <= n) put(d)
  else if (e.key === 'Backspace' || e.key === 'Delete' || e.key === '0') put(0)
  else if (sel.value && e.key.startsWith('Arrow')) {
    e.preventDefault()
    const { r, c } = sel.value
    const mv = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] }[e.key]
    sel.value = { r: (r + mv[0] + n) % n, c: (c + mv[1] + n) % n }
  }
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

function back() {
  if (window.history.state?.back) router.back()
  else router.push('/')
}
</script>

<template>
  <header class="bar-top">
    <button class="icon-btn" aria-label="返回" @click="back">‹</button>
    <span class="ttl">数独</span>
    <span class="chip-stat">✅ {{ state.sudoku.wins }}</span>
  </header>
  <p class="rule muted">
    每一行、每一列、每个粗线框里,1~{{ cfg.n }} 都要出现,而且只出现一次。
  </p>

  <div class="levels" role="group" aria-label="难度">
    <button class="chip" :class="{ on: !state.sudoku.hard }" :aria-pressed="!state.sudoku.hard" @click="setHard(false)">简单 4×4</button>
    <button class="chip" :class="{ on: state.sudoku.hard }" :aria-pressed="!!state.sudoku.hard" @click="setHard(true)">挑战 6×6</button>
  </div>

  <div class="grid" :class="[`n${cfg.n}`, { won }]" role="grid" :aria-label="`${cfg.n}×${cfg.n} 数独`">
    <template v-for="(row, r) in board" :key="r">
      <button
        v-for="(v, c) in row"
        :key="`${r}-${c}`"
        class="cell"
        :class="cellClass(r, c)"
        role="gridcell"
        :aria-label="`第 ${r + 1} 行第 ${c + 1} 列,${v || '空'}${given(r, c) ? ',题目给出' : ''}`"
        @click="pick(r, c)"
      >
        {{ v || '' }}
      </button>
    </template>
  </div>

  <p class="msg" :class="{ ok: won, bad: !won && conflicts.size }" role="status" aria-live="polite">
    <template v-if="msg">{{ msg }}</template>
    <template v-else-if="conflicts.size">有数字重复了,红色的格子再想想</template>
    <template v-else-if="!sel">点一个空格子,再点下面的数字</template>
    <template v-else>&nbsp;</template>
  </p>

  <div class="pad" :class="`n${cfg.n}`">
    <button v-for="d in cfg.n" :key="d" class="num" :disabled="won" @click="put(d)">{{ d }}</button>
    <button class="num erase" :disabled="won" aria-label="擦除" @click="put(0)">⌫</button>
  </div>

  <div class="tools">
    <button class="btn soft" :disabled="won || hints >= MAX_HINTS" @click="hint">💡 提示 {{ MAX_HINTS - hints }}</button>
    <button class="btn" :disabled="won" @click="clearAll">↺ 清空</button>
    <button class="btn primary" @click="fresh">{{ won ? '下一盘 →' : '换一盘' }}</button>
  </div>
</template>

<style scoped>
.bar-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: -4px 0 4px;
}
.icon-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  font-size: 30px;
  line-height: 1;
  margin-left: -8px;
}
.ttl {
  font-weight: 800;
  font-size: 22px;
  flex: 1;
}
.chip-stat {
  font-size: 13px;
  font-weight: 700;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 2px 10px;
}
.rule {
  font-size: 14px;
  margin: 0 0 10px;
}
.levels {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.grid {
  --n: 4;
  display: grid;
  grid-template-columns: repeat(var(--n), minmax(0, 1fr));
  width: min(100%, 360px);
  margin: 0 auto;
  border: 3px solid var(--text);
  border-radius: 12px;
  overflow: hidden;
  background: var(--card);
}
.grid.n6 {
  --n: 6;
}
.cell {
  aspect-ratio: 1;
  border: none;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  background: var(--card);
  font-size: 28px;
  font-weight: 700;
  color: var(--primary);
  padding: 0;
  font-variant-numeric: tabular-nums;
}
.n6 .cell {
  font-size: 22px;
}
.cell.br {
  border-right: 3px solid var(--text);
}
.cell.bb {
  border-bottom: 3px solid var(--text);
}
.cell.given {
  color: var(--text);
  font-weight: 800;
}
.cell.peer {
  background: var(--primary-soft);
  background: color-mix(in srgb, var(--primary) 7%, var(--card));
}
.cell.same {
  background: color-mix(in srgb, var(--primary) 20%, var(--card));
}
.cell.sel {
  background: color-mix(in srgb, var(--primary) 32%, var(--card));
}
.cell.bad {
  color: var(--bad);
  background: var(--bad-soft);
}
.grid.won .cell {
  background: var(--ok-soft);
  color: var(--ok);
}
.msg {
  min-height: 1.6em;
  text-align: center;
  font-weight: 600;
  margin: 10px 0;
}
.msg.ok {
  color: var(--ok);
  font-size: 18px;
}
.msg.bad {
  color: var(--bad);
}
.pad {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}
.pad.n6 {
  grid-template-columns: repeat(7, minmax(0, 1fr));
}
.num {
  height: 54px;
  border-radius: 14px;
  border: 2px solid var(--line);
  background: var(--card);
  font-size: 24px;
  font-weight: 800;
  color: var(--primary);
  box-shadow: 0 4px 0 var(--line);
}
.num:active {
  transform: translateY(2px);
  box-shadow: 0 2px 0 var(--line);
}
.num.erase {
  color: var(--muted);
  font-size: 20px;
}
.num:disabled {
  opacity: 0.45;
}
.tools {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.tools .btn {
  padding: 0 4px;
  font-size: 14px;
}
</style>
