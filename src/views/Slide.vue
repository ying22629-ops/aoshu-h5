<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { isSolved, scramble, slideFrom, solved } from '../slide.js'
import { state } from '../store.js'
import { GAME_STARS } from '../rewards.js'
import { sfx } from '../sfx.js'
import { confetti } from '../confetti.js'

const STEPS = { 3: 40, 4: 90 }
const router = useRouter()
const n = computed(() => (state.slide.size === 4 ? 4 : 3))
const tiles = ref([])
const moves = ref(0)
const won = ref(false)
const best = computed(() => state.slide[`best${n.value}`])

function fresh() {
  tiles.value = scramble(n.value, STEPS[n.value])
  moves.value = 0
  won.value = false
}
fresh()

const pos = computed(() => {
  const p = {}
  tiles.value.forEach((v, i) => (p[v] = i))
  return p
})
const order = computed(() => solved(n.value).filter(Boolean))

function tap(v) {
  if (won.value) return
  const res = slideFrom(tiles.value, n.value, pos.value[v])
  if (!res) return
  tiles.value = res.tiles
  moves.value += res.moved
  sfx.tap()
  if (isSolved(res.tiles)) win()
}

function win() {
  won.value = true
  const s = state.slide
  s[`wins${n.value}`] += 1
  const key = `best${n.value}`
  if (s[key] === null || moves.value < s[key]) s[key] = moves.value
  sfx.win()
  confetti(48)
}

function setSize(v) {
  if (n.value === v) return
  state.slide.size = v
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
    <span class="ttl">数字华容道</span>
    <span class="chip-stat">✅ {{ state.slide.wins3 + state.slide.wins4 }}</span>
  </header>
  <p class="rule muted">点和空格在同一行或同一列的方块,把它们滑过去。按 1、2、3……的顺序排好就赢啦!</p>

  <div class="levels" role="group" aria-label="大小">
    <button class="chip" :class="{ on: n === 3 }" :aria-pressed="n === 3" @click="setSize(3)">简单 3×3</button>
    <button class="chip" :class="{ on: n === 4 }" :aria-pressed="n === 4" @click="setSize(4)">挑战 4×4</button>
  </div>

  <div class="stats">
    <span>步数 <b>{{ moves }}</b></span>
    <span>最少 <b>{{ best ?? '—' }}</b></span>
  </div>

  <div class="board" :class="[`n${n}`, { won }]" :style="{ '--n': n }" role="group" aria-label="华容道棋盘">
    <button
      v-for="v in order"
      :key="v"
      class="tile"
      :class="{ home: pos[v] === v - 1 }"
      :style="{ transform: `translate(${(pos[v] % n) * 100}%, ${Math.floor(pos[v] / n) * 100}%)` }"
      :aria-label="`方块 ${v}`"
      @click="tap(v)"
    >
      <span>{{ v }}</span>
    </button>
  </div>

  <p class="msg" :class="{ ok: won }" role="status" aria-live="polite">
    {{ won ? `完成啦!用了 ${moves} 步,获得 ${GAME_STARS[`slide${n}`]} 颗星 ⭐` : '绿色的方块已经在正确位置' }}
  </p>

  <button class="btn primary wide" @click="fresh">{{ won ? '再来一局 →' : '重新打乱' }}</button>
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
  margin-bottom: 10px;
}
.stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  font-size: 15px;
  margin-bottom: 10px;
}
.stats b {
  font-size: 20px;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
}
.board {
  position: relative;
  width: min(100%, 340px);
  aspect-ratio: 1;
  margin: 0 auto;
  padding: 8px;
  border-radius: 20px;
  background: linear-gradient(160deg, #ea580c, #c2410c);
  box-shadow: inset 0 0 0 5px rgba(255, 255, 255, 0.15);
}
.tile {
  position: absolute;
  left: 8px;
  top: 8px;
  width: calc((100% - 16px) / var(--n));
  height: calc((100% - 16px) / var(--n));
  padding: 4px;
  border: none;
  background: none;
  transition: transform 0.16s ease-out;
}
.tile span {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  border-radius: 14px;
  background: #fffdf7;
  color: #1f2333;
  font-size: 34px;
  font-weight: 800;
  box-shadow: 0 5px 0 #d6d0bf;
  font-variant-numeric: tabular-nums;
}
.n4 .tile span {
  font-size: 26px;
  border-radius: 10px;
}
.tile.home span {
  background: #dcfce7;
  color: #15803d;
}
.board.won .tile span {
  background: linear-gradient(135deg, #fde68a, #f59e0b);
  color: #7c2d12;
}
.msg {
  min-height: 1.6em;
  text-align: center;
  font-weight: 600;
  margin: 12px 0;
}
.msg.ok {
  color: var(--ok);
  font-size: 17px;
}
.wide {
  width: 100%;
  min-height: 50px;
  font-size: 17px;
}
@media (prefers-reduced-motion: reduce) {
  .tile {
    transition: none;
  }
}
</style>
