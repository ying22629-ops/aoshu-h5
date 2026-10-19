<script setup>
import { computed } from 'vue'
import AiSettings from '../components/AiSettings.vue'
import InstallGuide from '../components/InstallGuide.vue'
import { topics, questions } from '../bank.js'
import { state, currentStreak, resetAll } from '../store.js'

const recs = computed(() => Object.entries(state.records))
const practiced = computed(() => recs.value.length)
const firstTryRate = computed(() => {
  if (!practiced.value) return '—'
  const ok = recs.value.filter(([, r]) => r.firstTry).length
  return Math.round((ok / practiced.value) * 100) + '%'
})
const perTopic = computed(() =>
  topics.map((t) => {
    const ids = questions.filter((q) => q.topic === t.id).map((q) => q.id)
    const done = ids.filter((id) => state.records[id])
    const ok = done.filter((id) => state.records[id].firstTry).length
    return { ...t, total: ids.length, done: done.length, rate: done.length ? ok / done.length : 0 }
  }),
)

function reset() {
  if (window.confirm('确定清空所有练习记录和错题吗?此操作无法撤销。')) resetAll()
}
</script>

<template>
  <header class="head">
    <h1>我的</h1>
  </header>

  <div class="stats">
    <div class="card stat"><b>{{ practiced }}</b><span class="muted">练过的题</span></div>
    <div class="card stat"><b>{{ firstTryRate }}</b><span class="muted">独立做对率</span></div>
    <div class="card stat"><b>{{ currentStreak() }}</b><span class="muted">连续打卡</span></div>
  </div>

  <h2 class="section">各专题掌握情况</h2>
  <div class="card">
    <div v-for="t in perTopic" :key="t.id" class="row">
      <span class="name">{{ t.name }}</span>
      <span class="bar" aria-hidden="true"><i :style="{ width: t.rate * 100 + '%' }"></i></span>
      <span class="muted num">{{ t.done ? Math.round(t.rate * 100) + '%' : '未练' }}</span>
    </div>
    <p class="muted note">“独立做对”= 第一次作答就正确且没有看提示。</p>
  </div>

  <h2 class="section">设置</h2>
  <div class="card">
    <label class="toggle">
      <span>🔊 音效</span>
      <input v-model="state.sound" type="checkbox" role="switch" />
    </label>
  </div>

  <h2 class="section">AI 老师</h2>
  <div class="card">
    <AiSettings />
  </div>

  <h2 class="section">添加到手机桌面</h2>
  <div class="card">
    <InstallGuide />
  </div>

  <h2 class="section">给家长</h2>
  <div class="card about">
    <p>本应用是小学数学思维训练的练习工具,题目按专题和年级整理,每题都配有分步提示和完整解析,鼓励孩子先独立思考。</p>
    <p>我们不收集任何个人信息,练习记录只保存在当前设备的浏览器里。清除浏览器数据或更换设备后,记录不会保留。</p>
    <p>使用 AI 老师时,当前题目、孩子的作答和提问内容会发送给 DeepSeek 生成讲解,不包含任何个人信息。AI 的回答可能出错,建议家长陪同使用。</p>
    <button class="btn danger" @click="reset">清空练习记录</button>
  </div>
</template>

<style scoped>
.head h1 {
  margin: 4px 0 14px;
  font-size: 26px;
}
.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 6px;
}
.stat b {
  font-size: 24px;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
}
.stat span {
  font-size: 12px;
}
.section {
  font-size: 17px;
  margin: 22px 0 10px;
}
.row {
  display: grid;
  grid-template-columns: 5.5em 1fr 3em;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  font-size: 14px;
}
.bar {
  height: 8px;
  border-radius: 4px;
  background: var(--line);
  overflow: hidden;
}
.bar i {
  display: block;
  height: 100%;
  background: var(--ok);
}
.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.note {
  font-size: 12px;
  margin: 8px 0 0;
}
.toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15px;
  min-height: 32px;
}
.toggle input {
  width: 22px;
  height: 22px;
  accent-color: var(--primary);
}
.about p {
  margin: 0 0 10px;
  font-size: 14px;
}
.danger {
  color: var(--bad);
}
</style>
