<script setup>
import { computed, ref } from 'vue'
import InstallGuide from '../components/InstallGuide.vue'
import { topics, questionsFor, dailyQuestion, getTopic, todayStr } from '../bank.js'
import { isMobile, isStandalone } from '../install.js'
import { state, currentStreak, starsOf } from '../store.js'
import { topicColor } from '../theme.js'
import Owl from '../components/Owl.vue'
import { balance, food } from '../rewards.js'

const showInstall = computed(() => isMobile && !isStandalone.value && !state.installTipClosed)
const installOpen = ref(false)

const grades = [
  { v: 0, label: '全部' },
  { v: 1, label: '一年级' },
  { v: 2, label: '二年级' },
  { v: 3, label: '三年级' },
  { v: 4, label: '四年级' },
  { v: 5, label: '五年级' },
  { v: 6, label: '六年级' },
]

const today = todayStr()
const daily = computed(() => dailyQuestion(today, state.grade))
const dailyDone = computed(() => state.daily.last === today)
const streak = computed(() => currentStreak())

const topicCards = computed(() =>
  topics
    .map((t) => {
      const list = questionsFor(t.id, state.grade)
      const stars = list.reduce((s, q) => s + (starsOf(q.id) ?? 0), 0)
      const done = list.filter((q) => starsOf(q.id) !== null).length
      return { ...t, total: list.length, done, stars, color: topicColor(t.id) }
    })
    .filter((t) => t.total > 0),
)
const greeting = (() => {
  const h = new Date().getHours()
  if (h < 11) return '早上好!'
  if (h < 14) return '中午好!'
  if (h < 18) return '下午好!'
  return '晚上好!'
})()
</script>

<template>
  <header class="hero">
    <div class="hero-text">
      <p class="hi">{{ greeting }}</p>
      <h1>思维数学</h1>
      <p class="tag-line">闯关做题,动动小脑筋 🧠</p>
    </div>
    <RouterLink to="/pet" class="hero-side" aria-label="去看看我的小智">
      <span class="owl" aria-hidden="true"><Owl :size="52" still /></span>
      <span class="star-total">⭐ {{ balance }}</span>
      <span v-if="food < 30" class="hungry" aria-hidden="true">饿了</span>
    </RouterLink>
  </header>

  <div v-if="showInstall" class="card install">
    <div class="install-top">
      <button class="install-open" :aria-expanded="installOpen" @click="installOpen = !installOpen">
        📲 添加到手机桌面,像 App 一样打开 <span class="muted">{{ installOpen ? '收起' : '怎么做?' }}</span>
      </button>
      <button class="close" aria-label="关闭提示" @click="state.installTipClosed = true">×</button>
    </div>
    <InstallGuide v-if="installOpen" class="install-body" />
  </div>

  <div class="grades" role="group" aria-label="选择年级">
    <button
      v-for="g in grades"
      :key="g.v"
      class="chip"
      :class="{ on: state.grade === g.v }"
      :aria-pressed="state.grade === g.v"
      @click="state.grade = g.v"
    >
      {{ g.label }}
    </button>
  </div>

  <RouterLink :to="`/practice/daily/${today}`" class="card daily">
    <span class="daily-ico" aria-hidden="true">📅</span>
    <div class="daily-main">
      <div class="daily-top">
        <span class="daily-title">每日一题</span>
        <span class="streak">{{ streak ? `🔥 连续 ${streak} 天` : '今天开始打卡' }}</span>
      </div>
      <p class="daily-sub muted">
        今日专题:{{ getTopic(daily.topic).name }} · {{ '★'.repeat(daily.difficulty) }}
      </p>
    </div>
    <span class="go" :class="{ done: dailyDone }">{{ dailyDone ? '✓' : 'GO' }}</span>
  </RouterLink>

  <h2 class="section">闯关岛屿</h2>
  <div class="grid">
    <RouterLink
      v-for="t in topicCards"
      :key="t.id"
      :to="`/map/${t.id}`"
      class="card topic"
      :style="{ '--tc': t.color }"
    >
      <span class="t-ico" aria-hidden="true">{{ t.icon }}</span>
      <span class="t-name">{{ t.name }}</span>
      <span class="t-desc muted">{{ t.desc }}</span>
      <span class="bar" role="progressbar" :aria-valuenow="t.done" :aria-valuemax="t.total" :aria-label="`${t.name}闯关进度`">
        <i :style="{ width: (t.done / t.total) * 100 + '%' }"></i>
      </span>
      <span class="t-prog">
        <span class="muted">{{ t.done }} / {{ t.total }} 关</span>
        <span class="t-stars">⭐ {{ t.stars }}</span>
      </span>
    </RouterLink>
  </div>

  <h2 class="section">思维游戏</h2>
  <div class="games">
    <RouterLink to="/game/24" class="card game g24">
      <span class="game-ico" aria-hidden="true">🃏</span>
      <span class="game-title">24 点</span>
      <span class="game-desc">加减乘除凑 24</span>
      <span class="game-stat">✅ {{ state.g24.solved }}</span>
    </RouterLink>
    <RouterLink to="/game/sudoku" class="card game gsd">
      <span class="game-ico" aria-hidden="true">🔢</span>
      <span class="game-title">数独</span>
      <span class="game-desc">练逻辑推理</span>
      <span class="game-stat">✅ {{ state.sudoku.wins }}</span>
    </RouterLink>
    <RouterLink to="/game/slide" class="card game gsl">
      <span class="game-ico" aria-hidden="true">🧩</span>
      <span class="game-title">华容道</span>
      <span class="game-desc">滑块排顺序</span>
      <span class="game-stat">✅ {{ state.slide.wins3 + state.slide.wins4 }}</span>
    </RouterLink>
  </div>
</template>

<style scoped>
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: -16px -16px 14px;
  padding: 20px 16px 22px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 55%, #ec4899 100%);
  color: #fff;
  border-radius: 0 0 26px 26px;
}
.hero h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.2;
}
.hi,
.tag-line {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}
.hero-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.owl {
  font-size: 46px;
  line-height: 1;
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  50% {
    transform: translateY(-5px) rotate(-4deg);
  }
}
.star-total {
  font-weight: 800;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.22);
  border-radius: 999px;
  padding: 2px 10px;
}
.install {
  padding: 10px 12px;
  margin-bottom: 12px;
  background: var(--warn-soft);
  border-color: transparent;
}
.install-top {
  display: flex;
  align-items: center;
  gap: 8px;
}
.install-open {
  flex: 1;
  text-align: left;
  border: none;
  background: none;
  padding: 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--warn-text);
}
.install-open .muted {
  font-weight: 400;
  margin-left: 4px;
}
.close {
  border: none;
  background: none;
  font-size: 22px;
  line-height: 1;
  width: 32px;
  height: 32px;
  color: var(--muted);
}
.install-body {
  margin-top: 6px;
}
.grades {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
  margin-bottom: 14px;
  scrollbar-width: none;
}
.grades .chip {
  flex: none;
}
.daily {
  display: flex;
  align-items: center;
  gap: 12px;
}
.daily-ico {
  font-size: 34px;
  line-height: 1;
}
.daily-main {
  flex: 1;
  min-width: 0;
}
.daily-top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.daily-title {
  font-size: 18px;
  font-weight: 800;
}
.streak {
  font-size: 12px;
  font-weight: 700;
  color: var(--warn-text);
  background: var(--warn-soft);
  border-radius: 999px;
  padding: 1px 8px;
}
.daily-sub {
  margin: 2px 0 0;
  font-size: 13px;
}
.go {
  flex: none;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-weight: 900;
  color: #fff;
  background: linear-gradient(135deg, #f97316, #ef4444);
  box-shadow: 0 4px 0 #b91c1c;
}
.go.done {
  background: var(--ok);
  box-shadow: 0 4px 0 color-mix(in srgb, var(--ok) 70%, #000);
  font-size: 22px;
}
.section {
  font-size: 18px;
  margin: 22px 0 10px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.topic {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 14px;
  border-top: 5px solid var(--tc);
  background: var(--card);
  background: linear-gradient(180deg, color-mix(in srgb, var(--tc) 12%, var(--card)), var(--card) 60%);
}
.topic:active {
  transform: scale(0.98);
}
.t-ico {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--tc);
  color: #fff;
  font-weight: 800;
  font-size: 20px;
  margin-bottom: 6px;
  box-shadow: 0 3px 0 color-mix(in srgb, var(--tc) 70%, #000);
}
.t-name {
  font-weight: 800;
}
.t-desc {
  font-size: 12px;
  line-height: 1.4;
  min-height: 2.8em;
}
.bar {
  display: block;
  height: 8px;
  border-radius: 4px;
  background: var(--line);
  overflow: hidden;
  margin-top: 8px;
}
.bar i {
  display: block;
  height: 100%;
  background: var(--tc);
  border-radius: 4px;
  transition: width 0.3s;
}
.t-prog {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-top: 2px;
}
.t-stars {
  font-weight: 700;
  color: var(--warn-text);
}
.hero-side {
  position: relative;
  color: inherit;
}
.hungry {
  position: absolute;
  top: -4px;
  right: -10px;
  font-size: 11px;
  font-weight: 800;
  background: #fff;
  color: var(--bad);
  border-radius: 999px;
  padding: 0 6px;
}
.games {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.game {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 2px;
  padding: 12px 6px;
  border-color: transparent;
  color: #fff;
}
.game:active {
  transform: scale(0.97);
}
.g24 {
  background: linear-gradient(150deg, #16a34a, #0d9488);
}
.gsd {
  background: linear-gradient(150deg, #6366f1, #3b82f6);
}
.gsl {
  background: linear-gradient(150deg, #f97316, #e11d48);
}
.game-ico {
  font-size: 32px;
  line-height: 1.1;
}
.game-title {
  font-size: 16px;
  font-weight: 800;
}
.game-desc {
  font-size: 11px;
  opacity: 0.9;
}
.game-stat {
  margin-top: 4px;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.22);
  border-radius: 999px;
  padding: 0 8px;
  font-size: 12px;
}
@media (prefers-reduced-motion: reduce) {
  .owl {
    animation: none;
  }
}
</style>
