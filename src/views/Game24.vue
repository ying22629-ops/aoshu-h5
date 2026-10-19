<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { OPS, apply, bestSolve, expression, frac, fracLabel, is24, newPuzzle } from '../game24.js'
import { state } from '../store.js'
import { sfx } from '../sfx.js'
import { confetti } from '../confetti.js'

const router = useRouter()
const puzzle = ref([])
const cards = ref([])
const history = ref([])
const sel = ref(null)
const op = ref(null)
const hintTarget = ref(null)
const status = ref('play')
const msg = ref('')
const answer = ref('')
const usedHelp = ref(false)
const shake = ref(false)
let nextId = 0

const g = computed(() => state.g24)
const max = computed(() => (g.value.hard ? 13 : 9))

function load(nums) {
  puzzle.value = nums
  history.value = []
  cards.value = nums.map((n) => ({ id: nextId++, v: frac(n), made: false }))
  sel.value = op.value = hintTarget.value = null
  status.value = 'play'
  msg.value = answer.value = ''
  usedHelp.value = false
}

function fresh() {
  load(newPuzzle(max.value))
}
fresh()

function nudge(text) {
  msg.value = text
  shake.value = true
  setTimeout(() => (shake.value = false), 400)
}

function tapCard(k) {
  if (status.value !== 'play') return
  sfx.tap()
  msg.value = ''
  hintTarget.value = null
  if (sel.value === null || op.value === null) {
    sel.value = sel.value === k ? null : k
    return
  }
  if (sel.value === k) {
    sel.value = null
    op.value = null
    return
  }
  combine(sel.value, op.value, k)
}

function tapOp(o) {
  if (status.value !== 'play') return
  if (sel.value === null) return nudge('先点一张数字牌')
  sfx.tap()
  op.value = op.value === o ? null : o
}

function combine(i, o, j) {
  const r = apply(cards.value[i].v, o, cards.value[j].v)
  if (!r) return nudge('不能除以 0 哦')
  history.value.push(cards.value)
  const made = { id: nextId++, v: r, made: true }
  const nextCards = cards.value.map((c, k) => (k === j ? made : c)).filter((_, k) => k !== i)
  cards.value = nextCards
  sel.value = nextCards.indexOf(made)
  op.value = null
  if (nextCards.length === 1) finish(r)
}

function finish(r) {
  sel.value = null
  if (is24(r)) {
    status.value = 'won'
    g.value.solved += 1
    if (!usedHelp.value) {
      g.value.streak += 1
      g.value.best = Math.max(g.value.best, g.value.streak)
    }
    msg.value = usedHelp.value ? '算出 24 啦!下次试试不看提示~' : pick(['太厉害了!', '算出 24 啦!', '你是计算小能手!'])
    sfx.win()
    confetti(48)
  } else {
    status.value = 'stuck'
    msg.value = `结果是 ${fracLabel(r)},不是 24。撤销一步再试试!`
    sfx.wrong()
  }
}

const pick = (arr) => arr[Math.floor(Math.random() * arr.length)]

function undo() {
  if (!history.value.length || status.value === 'won') return
  cards.value = history.value.pop()
  sel.value = op.value = hintTarget.value = null
  status.value = 'play'
  msg.value = ''
}

function restart() {
  load(puzzle.value)
}

function hint() {
  if (status.value !== 'play') return
  const steps = bestSolve(cards.value.map((c) => c.v))
  usedHelp.value = true
  if (!steps) return nudge('这条路走不通了,撤销一步试试')
  const [first] = steps
  sel.value = first.i
  op.value = first.op
  hintTarget.value = first.j
  msg.value = `试试:${fracLabel(cards.value[first.i].v)} ${first.op} ${fracLabel(cards.value[first.j].v)}`
}

function showAnswer() {
  const vals = puzzle.value.map((n) => frac(n))
  answer.value = `${expression(vals, bestSolve(vals))} = 24`
  status.value = 'shown'
  usedHelp.value = true
  g.value.streak = 0
  msg.value = ''
}

function next() {
  if (status.value !== 'won') g.value.streak = 0
  fresh()
}

function setHard(v) {
  if (g.value.hard === v) return
  g.value.hard = v
  fresh()
}

function back() {
  if (window.history.state?.back) router.back()
  else router.push('/')
}
</script>

<template>
  <header class="bar-top">
    <button class="icon-btn" aria-label="返回" @click="back">‹</button>
    <span class="ttl">24 点</span>
    <span class="chip-stat">✅ {{ g.solved }}</span>
    <span class="chip-stat hot" :title="`最高连胜 ${g.best}`">🔥 {{ g.streak }}</span>
  </header>
  <p class="rule muted">用 4 个数和 + − × ÷ 算出 <b>24</b>,每个数都要用,而且只能用一次。</p>

  <div class="levels" role="group" aria-label="难度">
    <button class="chip" :class="{ on: !g.hard }" :aria-pressed="!g.hard" @click="setHard(false)">简单 1~9</button>
    <button class="chip" :class="{ on: g.hard }" :aria-pressed="!!g.hard" @click="setHard(true)">挑战 1~13</button>
  </div>

  <section class="table" :class="{ shake, won: status === 'won' }">
    <div class="cards" :class="`n${cards.length}`">
      <button
        v-for="(c, k) in cards"
        :key="c.id"
        class="pcard"
        :class="{ sel: sel === k, target: hintTarget === k, made: c.made, gold: status === 'won' }"
        :aria-pressed="sel === k"
        :aria-label="`数字 ${fracLabel(c.v)}`"
        @click="tapCard(k)"
      >
        {{ fracLabel(c.v) }}
      </button>
    </div>
  </section>

  <div class="ops" role="group" aria-label="运算符">
    <button
      v-for="o in OPS"
      :key="o"
      class="op"
      :class="{ on: op === o }"
      :aria-pressed="op === o"
      :disabled="status !== 'play'"
      @click="tapOp(o)"
    >
      {{ o }}
    </button>
  </div>

  <p class="msg" :class="status" role="status" aria-live="polite">
    <template v-if="answer">答案:{{ answer }}</template>
    <template v-else-if="msg">{{ msg }}</template>
    <template v-else-if="sel === null">点一张数字牌开始</template>
    <template v-else-if="op === null">再点一个运算符</template>
    <template v-else>再点另一张数字牌</template>
  </p>

  <div class="tools">
    <button class="btn" :disabled="!history.length || status === 'won'" @click="undo">↶ 撤销</button>
    <button class="btn" :disabled="status === 'won'" @click="restart">↺ 重来</button>
    <button class="btn soft" :disabled="status !== 'play'" @click="hint">💡 提示</button>
    <button class="btn" :disabled="status === 'won' || status === 'shown'" @click="showAnswer">答案</button>
  </div>

  <button class="btn primary wide" @click="next">{{ status === 'won' || status === 'shown' ? '下一题 →' : '换一题' }}</button>
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
.chip-stat.hot {
  background: var(--warn-soft);
  color: var(--warn-text);
  border-color: transparent;
}
.rule {
  font-size: 14px;
  margin: 0 0 10px;
}
.rule b {
  color: var(--primary);
}
.levels {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.table {
  background: linear-gradient(160deg, #16a34a, #15803d);
  border-radius: 22px;
  padding: 18px;
  min-height: 268px;
  display: grid;
  place-items: center;
  box-shadow: inset 0 0 0 6px rgba(255, 255, 255, 0.12);
}
.cards {
  display: grid;
  grid-template-columns: repeat(2, 108px);
  gap: 14px;
  justify-content: center;
}
.cards.n3 {
  grid-template-columns: repeat(3, 92px);
}
.cards.n1 {
  grid-template-columns: 140px;
}
.pcard {
  height: 108px;
  border: none;
  border-radius: 16px;
  background: #fffdf7;
  color: #1f2333;
  font-size: 40px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  box-shadow: 0 6px 0 #d6d0bf, 0 10px 18px rgba(0, 0, 0, 0.25);
  transition: transform 0.15s, box-shadow 0.15s, background 0.2s;
  position: relative;
}
.n3 .pcard {
  height: 96px;
  font-size: 32px;
}
.n1 .pcard {
  height: 130px;
  font-size: 52px;
}
.pcard.made {
  background: #fff4d6;
}
.pcard.sel {
  transform: translateY(-8px);
  box-shadow: 0 0 0 4px #facc15, 0 12px 20px rgba(0, 0, 0, 0.3);
}
.pcard.target {
  animation: glow 1s ease-in-out infinite;
}
.pcard.gold {
  background: linear-gradient(135deg, #fde68a, #f59e0b);
  color: #7c2d12;
}
@keyframes glow {
  50% {
    box-shadow: 0 0 0 4px #60a5fa, 0 6px 0 #d6d0bf;
  }
}
.pcard.made {
  animation: appear 0.28s cubic-bezier(0.3, 1.6, 0.5, 1);
}
@keyframes appear {
  from {
    transform: scale(0.4);
    opacity: 0;
  }
}
.ops {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 16px 0 8px;
}
.op {
  height: 60px;
  border-radius: 16px;
  border: 2px solid var(--line);
  background: var(--card);
  font-size: 30px;
  font-weight: 800;
  color: var(--primary);
  box-shadow: 0 4px 0 var(--line);
}
.op.on {
  background: var(--primary);
  color: var(--on-primary);
  border-color: var(--primary);
  transform: translateY(2px);
  box-shadow: 0 2px 0 var(--line);
}
.op:disabled {
  opacity: 0.45;
}
.msg {
  min-height: 1.6em;
  text-align: center;
  font-weight: 600;
  margin: 4px 0 10px;
}
.msg.won {
  color: var(--ok);
  font-size: 18px;
}
.msg.stuck {
  color: var(--bad);
}
.msg.shown {
  color: var(--primary);
}
.tools {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}
.tools .btn {
  padding: 0 4px;
  font-size: 14px;
}
.wide {
  width: 100%;
  min-height: 50px;
  font-size: 17px;
}
.shake {
  animation: shake 0.35s;
}
@keyframes shake {
  25% {
    transform: translateX(-6px);
  }
  75% {
    transform: translateX(6px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .shake,
  .pcard.target,
  .pcard.made {
    animation: none;
  }
}
@media (max-width: 360px) {
  .cards {
    grid-template-columns: repeat(2, 96px);
  }
  .cards.n3 {
    grid-template-columns: repeat(3, 80px);
  }
}
</style>
