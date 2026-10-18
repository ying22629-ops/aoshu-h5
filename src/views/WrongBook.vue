<script setup>
import { computed } from 'vue'
import MathText from '../components/MathText.vue'
import { getQuestion, getTopic } from '../bank.js'
import { state } from '../store.js'

const items = computed(() =>
  Object.entries(state.wrong)
    .map(([id, w]) => ({ q: getQuestion(id), ...w }))
    .filter((x) => x.q)
    .sort((a, b) => b.addedAt - a.addedAt),
)

const fmt = (t) => {
  const d = new Date(t)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}
</script>

<template>
  <header class="head">
    <h1>错题本</h1>
    <p class="muted">复习时一次做对,就会自动移出错题本</p>
  </header>

  <div v-if="!items.length" class="empty">
    <div class="big">📒</div>
    <p>还没有错题,继续保持!</p>
    <RouterLink to="/" class="btn primary">去练习</RouterLink>
  </div>

  <template v-else>
    <RouterLink to="/practice/review/all" class="btn primary all">全部重做({{ items.length }} 题)</RouterLink>
    <ul class="list">
      <li v-for="it in items" :key="it.q.id">
        <RouterLink :to="`/practice/review/${it.q.id}`" class="card item">
          <div class="meta">
            <span class="tag">{{ getTopic(it.q.topic).name }}</span>
            <span class="muted">{{ fmt(it.addedAt) }} 加入 · 复习 {{ it.reviews }} 次</span>
          </div>
          <MathText :text="it.q.stem" class="stem" />
        </RouterLink>
      </li>
    </ul>
  </template>
</template>

<style scoped>
.head h1 {
  margin: 4px 0 0;
  font-size: 26px;
}
.head p {
  margin: 0 0 14px;
  font-size: 14px;
}
.all {
  width: 100%;
}
.list {
  list-style: none;
  padding: 0;
  margin: 14px 0 0;
  display: grid;
  gap: 10px;
}
.item {
  display: block;
}
.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  margin-bottom: 6px;
}
.stem {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 15px;
}
</style>
