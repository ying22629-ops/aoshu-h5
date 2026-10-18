<script setup>
import { computed } from 'vue'
import { topics, questionsFor, dailyQuestion, getTopic, todayStr } from '../bank.js'
import { state, currentStreak } from '../store.js'

const grades = [
  { v: 0, label: '全部' },
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
      const done = list.filter((q) => state.records[q.id]?.correct > 0).length
      return { ...t, total: list.length, done }
    })
    .filter((t) => t.total > 0),
)
</script>

<template>
  <header class="head">
    <h1>思维数学</h1>
    <p class="muted">每天一点点,思维更灵活</p>
  </header>

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
    <div class="daily-top">
      <span class="daily-title">每日一题</span>
      <span class="streak">{{ streak ? `🔥 连续 ${streak} 天` : '今天开始打卡' }}</span>
    </div>
    <p class="daily-sub muted">
      今日专题:{{ getTopic(daily.topic).name }} · {{ '★'.repeat(daily.difficulty) }}
    </p>
    <span class="btn" :class="dailyDone ? 'soft' : 'primary'">{{ dailyDone ? '已完成 ✓ 再看看' : '开始挑战' }}</span>
  </RouterLink>

  <h2 class="section">专题练习</h2>
  <div class="grid">
    <RouterLink v-for="t in topicCards" :key="t.id" :to="`/practice/topic/${t.id}`" class="card topic">
      <span class="t-ico" aria-hidden="true">{{ t.icon }}</span>
      <span class="t-name">{{ t.name }}</span>
      <span class="t-desc muted">{{ t.desc }}</span>
      <span class="bar" role="progressbar" :aria-valuenow="t.done" :aria-valuemax="t.total" :aria-label="`${t.name}进度`">
        <i :style="{ width: (t.done / t.total) * 100 + '%' }"></i>
      </span>
      <span class="t-prog muted">{{ t.done }} / {{ t.total }} 题</span>
    </RouterLink>
  </div>
</template>

<style scoped>
.head h1 {
  margin: 4px 0 0;
  font-size: 26px;
}
.head p {
  margin: 0 0 12px;
  font-size: 14px;
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
  display: block;
  background: linear-gradient(135deg, var(--primary-soft), var(--card) 70%);
}
.daily-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.daily-title {
  font-size: 19px;
  font-weight: 700;
}
.streak {
  font-size: 13px;
  font-weight: 600;
  color: var(--warn-text);
  background: var(--warn-soft);
  border-radius: 999px;
  padding: 2px 10px;
}
.daily-sub {
  margin: 4px 0 12px;
  font-size: 14px;
}
.section {
  font-size: 17px;
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
}
.t-ico {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: var(--primary-soft);
  color: var(--primary);
  font-weight: 700;
  font-size: 18px;
  margin-bottom: 6px;
}
.t-name {
  font-weight: 700;
}
.t-desc {
  font-size: 12px;
  line-height: 1.4;
  min-height: 2.8em;
}
.bar {
  display: block;
  height: 6px;
  border-radius: 3px;
  background: var(--line);
  overflow: hidden;
  margin-top: 8px;
}
.bar i {
  display: block;
  height: 100%;
  background: var(--primary);
  border-radius: 3px;
  transition: width 0.3s;
}
.t-prog {
  font-size: 12px;
}
</style>
