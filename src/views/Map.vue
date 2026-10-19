<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getTopic, questionsFor } from '../bank.js'
import { starsOf, state } from '../store.js'
import { topicColor } from '../theme.js'

const props = defineProps({ topic: String })
const router = useRouter()

const topic = computed(() => getTopic(props.topic))
const color = computed(() => topicColor(props.topic))
const STEP = 96
const XS = [50, 76, 50, 24]

const levels = computed(() => {
  const list = questionsFor(props.topic, state.grade)
  let open = true
  return list.map((q, i) => {
    const stars = starsOf(q.id)
    const level = { q, n: i + 1, stars, locked: !open, current: open && stars === null, x: XS[i % XS.length], y: 48 + i * STEP }
    open = stars !== null
    return level
  })
})
const height = computed(() => 48 + levels.value.length * STEP + 40)
const earned = computed(() => levels.value.reduce((s, l) => s + (l.stars ?? 0), 0))
const allDone = computed(() => levels.value.length > 0 && levels.value.every((l) => l.stars !== null))
const path = computed(() => {
  const pts = levels.value.map((l) => [l.x, l.y])
  if (!pts.length) return ''
  return pts.reduce((d, [x, y], i) => {
    if (i === 0) return `M${x} ${y}`
    const [px, py] = pts[i - 1]
    const my = (py + y) / 2
    return `${d} C${px} ${my} ${x} ${my} ${x} ${y}`
  }, '')
})

function play(l) {
  if (l.locked) return
  router.push({ path: `/practice/topic/${props.topic}`, query: { from: l.q.id } })
}

function back() {
  if (window.history.state?.back) router.back()
  else router.push('/')
}
</script>

<template>
  <div class="map" :style="{ '--tc': color }">
    <header class="bar-top">
      <button class="icon-btn" aria-label="返回" @click="back">‹</button>
      <span class="ttl">{{ topic?.name }}</span>
      <span class="total" :aria-label="`共获得 ${earned} 颗星`">⭐ {{ earned }} / {{ levels.length * 3 }}</span>
    </header>
    <p class="muted sub">{{ topic?.desc }} · 一次做对不看提示得 3 颗星</p>

    <div v-if="!levels.length" class="empty">
      <div class="big">🗺️</div>
      <p>这个年级还没有这个专题的关卡</p>
    </div>

    <div v-else class="board" :style="{ height: height + 'px' }">
      <svg class="road" :viewBox="`0 0 100 ${height}`" preserveAspectRatio="none" aria-hidden="true">
        <path :d="path" class="road-bg" />
        <path :d="path" class="road-dash" />
      </svg>
      <button
        v-for="l in levels"
        :key="l.q.id"
        class="node"
        :class="{ locked: l.locked, current: l.current, done: l.stars !== null }"
        :style="{ left: l.x + '%', top: l.y + 'px' }"
        :disabled="l.locked"
        :aria-label="`第 ${l.n} 关${l.locked ? ',未解锁' : l.stars !== null ? `,${l.stars} 颗星` : ',可以挑战'}`"
        @click="play(l)"
      >
        <span class="disc">{{ l.locked ? '🔒' : l.n }}</span>
        <span v-if="l.stars !== null" class="stars" aria-hidden="true">
          <i v-for="s in 3" :key="s" :class="{ on: s <= l.stars }">★</i>
        </span>
        <span v-else-if="l.current" class="go">开始</span>
      </button>
      <div class="goal" :class="{ reached: allDone }" :style="{ top: height - 40 + 'px' }" aria-hidden="true">
        {{ allDone ? '🏆 通关啦!' : '🏁' }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.bar-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: -4px 0 0;
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
  font-size: 20px;
  flex: 1;
}
.total {
  font-weight: 700;
  font-size: 14px;
  background: var(--warn-soft);
  color: var(--warn-text);
  padding: 2px 10px;
  border-radius: 999px;
}
.sub {
  font-size: 13px;
  margin: 2px 0 8px;
}
.board {
  position: relative;
  border-radius: 20px;
  background: var(--primary-soft);
  background: color-mix(in srgb, var(--tc) 10%, var(--bg));
}
.road {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.road-bg {
  fill: none;
  stroke: var(--card);
  stroke-width: 22;
  stroke-linecap: round;
  vector-effect: non-scaling-stroke;
}
.road-dash {
  fill: none;
  stroke: var(--tc);
  stroke-opacity: 0.45;
  stroke-width: 3;
  stroke-dasharray: 2 10;
  stroke-linecap: round;
  vector-effect: non-scaling-stroke;
}
.node {
  position: absolute;
  transform: translate(-50%, -50%);
  border: none;
  background: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.disc {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 22px;
  font-weight: 800;
  color: #fff;
  background: var(--tc);
  box-shadow: 0 5px 0 color-mix(in srgb, var(--tc) 70%, #000), 0 8px 16px rgba(0, 0, 0, 0.15);
  transition: transform 0.15s;
}
.node:active .disc {
  transform: translateY(3px);
}
.node.locked .disc {
  background: var(--line);
  color: var(--muted);
  font-size: 20px;
  box-shadow: 0 4px 0 var(--muted);
}
.node.current .disc {
  animation: bounce 1.4s ease-in-out infinite;
}
@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}
.stars {
  font-size: 15px;
  letter-spacing: 1px;
  line-height: 1;
  background: var(--card);
  border-radius: 999px;
  padding: 2px 6px;
}
.stars i {
  font-style: normal;
  color: var(--line);
}
.stars i.on {
  color: #f59e0b;
}
.go {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: var(--tc);
  border-radius: 999px;
  padding: 1px 10px;
}
.goal {
  position: absolute;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 26px;
  font-weight: 800;
  white-space: nowrap;
}
.goal.reached {
  font-size: 20px;
  color: var(--warn-text);
}
@media (prefers-reduced-motion: reduce) {
  .node.current .disc {
    animation: none;
  }
}
</style>
