<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MathText from '../components/MathText.vue'
import QFigure from '../components/QFigure.vue'
import AiTutor from '../components/AiTutor.vue'
import { aiReady } from '../ai.js'
import { dailyQuestion, getQuestion, getTopic, isCorrect, questionsFor } from '../bank.js'
import { finishDaily, markGaveUp, recordAttempt, recordStars, starsFor, state } from '../store.js'
import { sfx } from '../sfx.js'
import { confetti } from '../confetti.js'
import { topicColor } from '../theme.js'

const props = defineProps({ mode: String, id: String })
const route = useRoute()
const router = useRouter()
const combo = ref(0)
const earned = ref(0)
const cheer = ref('')
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)]
const WRONG_CHEERS = ['差一点点,再想想!', '别急,换个思路试试', '加油,你可以的!', '再检查一下哦']
const RIGHT_CHEERS = { 3: ['太棒了,一次就对!', '厉害!满分三颗星!', '思维小达人!'], 2: ['做对啦!', '真不错!'], 1: ['坚持到底,做对啦!'] }

const list = ref([])
const idx = ref(0)
const results = ref([])
const finished = ref(false)
const toast = ref('')
const shake = ref(false)
const cur = reactive({ answer: '', hints: 0, status: 'answering', attempts: 0, wrongAnswers: [] })

function build() {
  if (props.mode === 'topic') return questionsFor(props.id, state.grade)
  if (props.mode === 'daily') return [dailyQuestion(props.id, state.grade)]
  if (props.mode === 'review') {
    const ids = props.id === 'all' ? Object.keys(state.wrong) : [props.id]
    return ids.map(getQuestion).filter(Boolean)
  }
  return []
}

function resetQuestion() {
  Object.assign(cur, { answer: '', hints: 0, status: 'answering', attempts: 0, wrongAnswers: [] })
}

function start() {
  list.value = build()
  const from = props.mode === 'topic' ? list.value.findIndex((x) => x.id === route.query.from) : -1
  idx.value = Math.max(0, from)
  results.value = []
  finished.value = false
  combo.value = 0
  resetQuestion()
}
watch(() => [props.mode, props.id, route.query.from], start, { immediate: true })

function settle() {
  const stars = starsFor(cur)
  earned.value = stars
  recordStars(q.value.id, stars)
  const r = results.value.find((x) => x.id === q.value.id)
  if (r) r.stars = stars
  if (stars === 3) {
    combo.value += 1
    confetti()
  } else combo.value = 0
  if (cur.status === 'correct') {
    cheer.value = pick(RIGHT_CHEERS[stars])
    sfx.correct()
    for (let i = 0; i < stars; i++) setTimeout(() => sfx.star(i), 380 + i * 160)
  }
}

const q = computed(() => list.value[idx.value])
const title = computed(() => {
  if (props.mode === 'topic') return getTopic(props.id)?.name ?? '练习'
  if (props.mode === 'daily') return '每日一题'
  return '错题复习'
})
const locked = computed(() => cur.status === 'correct' || cur.status === 'revealed')
const canReveal = computed(() => cur.attempts > 0 || cur.hints >= (q.value?.hints.length ?? 0))
const firstTryRight = computed(() => results.value.filter((r) => r.ok).length)
const sessionStars = computed(() => results.value.reduce((s, r) => s + (r.stars ?? 0), 0))
const isLevel = computed(() => props.mode === 'topic')
const missed = computed(() => results.value.filter((r) => !r.ok))

function flash(msg) {
  toast.value = msg
  setTimeout(() => (toast.value = ''), 1800)
}

function submit() {
  if (locked.value || !cur.answer) return
  const ok = isCorrect(q.value, cur.answer)
  const first = cur.attempts === 0
  cur.attempts += 1
  const { mastered } = recordAttempt(q.value.id, ok, {
    hintsUsed: cur.hints,
    review: props.mode === 'review' && first,
  })
  if (first) results.value.push({ id: q.value.id, ok, stars: 0 })
  if (ok) {
    cur.status = 'correct'
    settle()
    if (mastered) flash('已掌握,移出错题本 🎉')
    if (props.mode === 'daily') finishDaily()
  } else {
    cur.status = 'wrong'
    cur.wrongAnswers.push(cur.answer)
    cheer.value = pick(WRONG_CHEERS)
    combo.value = 0
    sfx.wrong()
    shake.value = true
    setTimeout(() => (shake.value = false), 400)
  }
}

function choose(opt) {
  if (locked.value) return
  cur.answer = opt
  submit()
}

function press(k) {
  if (locked.value) return
  if (cur.status === 'wrong') cur.status = 'answering'
  if (k === 'del') cur.answer = cur.answer.slice(0, -1)
  else if (cur.answer.length < 12) cur.answer += k
}

function showHint() {
  if (cur.hints < q.value.hints.length) cur.hints += 1
}

function reveal() {
  if (cur.status === 'correct') return
  cur.status = 'revealed'
  if (cur.attempts === 0) results.value.push({ id: q.value.id, ok: false, stars: 0 })
  markGaveUp(q.value.id)
  settle()
  if (props.mode === 'daily') finishDaily()
}

function next() {
  if (idx.value + 1 >= list.value.length) {
    finished.value = true
    return
  }
  idx.value += 1
  resetQuestion()
}

function back() {
  if (window.history.state?.back) router.back()
  else router.push('/')
}

function onKey(e) {
  if (finished.value || !q.value || e.metaKey || e.ctrlKey || e.altKey) return
  if (e.key === 'Enter') {
    if (e.target instanceof HTMLButtonElement) return
    e.preventDefault()
    locked.value ? next() : submit()
    return
  }
  if (q.value.type !== 'input') return
  if (/^[0-9./]$/.test(e.key)) press(e.key)
  else if (e.key === 'Backspace') press('del')
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '0', '/']
</script>

<template>
  <header class="bar-top">
    <button class="icon-btn" aria-label="返回" @click="back">‹</button>
    <span class="ttl">{{ title }}</span>
    <span class="count muted" v-if="list.length && !finished">
      {{ isLevel ? `第 ${idx + 1} 关` : `${idx + 1} / ${list.length}` }}
    </span>
  </header>
  <div v-if="list.length > 1 && !finished" class="progress" aria-hidden="true">
    <i :style="{ width: (idx / list.length) * 100 + '%' }"></i>
  </div>

  <div v-if="!list.length" class="empty">
    <div class="big">🎉</div>
    <p>{{ mode === 'review' ? '错题本是空的,太棒了!' : '这里还没有题目' }}</p>
    <RouterLink to="/" class="btn primary">去练习</RouterLink>
  </div>

  <section v-else-if="finished" class="card summary">
    <div class="trophy" aria-hidden="true">{{ firstTryRight === results.length ? '🏆' : '🎖️' }}</div>
    <div class="score">⭐ {{ sessionStars }}<small> / {{ results.length * 3 }}</small></div>
    <p class="muted">本轮获得的星星 · 首次答对 {{ firstTryRight }} / {{ results.length }} 题</p>
    <p v-if="firstTryRight === results.length" class="praise">全部做对,厉害!</p>
    <p v-else class="praise">做错的题已经放进错题本,记得回来复习哦。</p>
    <ul class="res-list">
      <li v-for="r in results" :key="r.id">
        <span class="res-stars" :aria-label="`${r.stars} 颗星`">
          <i v-for="s in 3" :key="s" :class="{ on: s <= r.stars }">★</i>
        </span>
        <MathText :text="getQuestion(r.id).stem" class="res-stem" />
      </li>
    </ul>
    <div class="actions">
      <RouterLink v-if="isLevel" :to="`/map/${id}`" class="btn soft">返回地图</RouterLink>
      <button v-else-if="mode !== 'daily'" class="btn soft" @click="start">再练一遍</button>
      <RouterLink v-if="missed.length && mode !== 'review'" to="/wrong" class="btn soft">去错题本</RouterLink>
      <RouterLink to="/" class="btn primary">返回首页</RouterLink>
    </div>
  </section>

  <template v-else>
    <section class="card qcard" :class="{ shake }" :style="{ borderTopColor: topicColor(q.topic) }">
      <div class="meta">
        <span class="tag">{{ getTopic(q.topic).name }}</span>
        <span class="muted">{{ q.grade }} 年级 · <span :aria-label="`难度 ${q.difficulty}`">{{ '★'.repeat(q.difficulty) }}</span></span>
      </div>
      <p class="stem"><MathText :text="q.stem" /></p>
      <QFigure v-if="q.figure" :name="q.figure" />


      <div v-if="q.type === 'choice'" class="options">
        <button
          v-for="opt in q.options"
          :key="opt"
          class="option"
          :class="{
            right: locked && opt === q.answer,
            wrong: cur.status === 'wrong' && opt === cur.answer,
          }"
          :disabled="locked"
          @click="choose(opt)"
        >
          {{ opt }}
        </button>
      </div>

      <div
        v-else
        class="answer-box"
        :class="cur.status"
        role="textbox"
        aria-readonly="true"
        :aria-label="`你的答案:${cur.answer || '未填写'}`"
      >
        <span v-if="cur.answer">{{ cur.answer }}</span>
        <span v-else class="muted">用下方键盘输入答案</span>
        <span v-if="!locked" class="caret" aria-hidden="true"></span>
      </div>

      <p v-if="cur.status === 'wrong'" class="feedback bad" role="status">🤔 {{ cheer }}可以看看提示。</p>
      <div v-if="cur.status === 'correct'" class="win" role="status">
        <span class="win-stars" :aria-label="`获得 ${earned} 颗星`">
          <i v-for="s in 3" :key="s" :class="{ on: s <= earned }" :style="{ animationDelay: 0.35 + s * 0.16 + 's' }">★</i>
        </span>
        <span class="feedback ok">{{ cheer }}</span>
        <span v-if="combo >= 2" class="combo">🔥 连对 ×{{ combo }}</span>
      </div>
    </section>

    <section v-if="cur.hints > 0" class="hints">
      <div v-for="(h, i) in q.hints.slice(0, cur.hints)" :key="i" class="hint">
        <b>提示 {{ i + 1 }}</b>
        <MathText :text="h" />
      </div>
    </section>

    <section v-if="locked" class="card solution">
      <b>解析</b>
      <p v-if="cur.status === 'revealed'" class="muted ans-line">正确答案:<strong>{{ q.answer }}</strong></p>
      <p><MathText :text="q.solution" /></p>
      <QFigure v-if="q.solutionFigure" :name="q.solutionFigure" label="解析配图" />
    </section>

    <AiTutor v-if="aiReady()" :key="q.id" :q="q" :status="cur.status" :wrong-answers="cur.wrongAnswers" />

    <div class="tools" v-if="!locked">
      <button class="btn soft" :disabled="cur.hints >= q.hints.length" @click="showHint">
        💡 提示 {{ cur.hints }}/{{ q.hints.length }}
      </button>
      <button class="btn" :disabled="!canReveal" @click="reveal">查看解析</button>
    </div>
    <p v-if="!locked && !canReveal" class="tip muted">先试着作答,或看完全部提示后才能查看解析</p>

    <div v-if="q.type === 'input' && !locked" class="keypad">
      <button v-for="k in keys" :key="k" class="key" @click="press(k)">{{ k }}</button>
      <button class="key fn" aria-label="删除" @click="press('del')">⌫</button>
      <button class="key submit" :disabled="!cur.answer" @click="submit">提交</button>
    </div>

    <div v-if="locked" class="next">
      <button class="btn primary wide" @click="next">
        {{ idx + 1 >= list.length ? '完成' : isLevel ? '下一关 →' : '下一题' }}
      </button>
    </div>
  </template>

  <div v-if="toast" class="toast" role="status">{{ toast }}</div>
</template>

<style scoped>
.bar-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: -4px 0 10px;
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
  font-weight: 700;
  font-size: 18px;
  flex: 1;
}
.count {
  font-size: 14px;
}
.progress {
  height: 4px;
  background: var(--line);
  border-radius: 2px;
  margin-bottom: 14px;
  overflow: hidden;
}
.progress i {
  display: block;
  height: 100%;
  background: var(--primary);
  transition: width 0.3s;
}
.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}
.stem {
  font-size: 18px;
  line-height: 1.8;
  margin: 12px 0 16px;
}
.answer-box {
  min-height: 52px;
  border: 2px solid var(--line);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 22px;
  font-weight: 600;
  display: flex;
  align-items: center;
  font-variant-numeric: tabular-nums;
}
.answer-box .muted {
  font-size: 15px;
  font-weight: 400;
}
.answer-box.correct {
  border-color: var(--ok);
  background: var(--ok-soft);
}
.answer-box.wrong {
  border-color: var(--bad);
  background: var(--bad-soft);
}
.caret {
  width: 2px;
  height: 24px;
  background: var(--primary);
  margin-left: 2px;
  animation: blink 1s steps(1) infinite;
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}
.options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.option {
  min-height: 52px;
  border: 2px solid var(--line);
  border-radius: 12px;
  background: var(--card);
  font-size: 18px;
  font-weight: 600;
}
.option.right {
  border-color: var(--ok);
  background: var(--ok-soft);
  color: var(--ok);
}
.option.wrong {
  border-color: var(--bad);
  background: var(--bad-soft);
  color: var(--bad);
}
.option:disabled {
  cursor: default;
}
.feedback {
  margin: 10px 0 0;
  font-weight: 600;
}
.qcard {
  border-top: 5px solid var(--primary);
}
.win {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 10px;
  margin-top: 10px;
}
.win .feedback {
  margin: 0;
}
.win-stars i,
.res-stars i {
  font-style: normal;
  color: var(--line);
}
.win-stars i {
  display: inline-block;
  font-size: 30px;
  line-height: 1;
  animation: pop 0.45s backwards;
}
.win-stars i.on,
.res-stars i.on {
  color: #f59e0b;
}
@keyframes pop {
  0% {
    transform: scale(0) rotate(-40deg);
    opacity: 0;
  }
  70% {
    transform: scale(1.35) rotate(8deg);
    opacity: 1;
  }
  100% {
    transform: scale(1);
  }
}
.combo {
  font-size: 13px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(90deg, #f97316, #ef4444);
  border-radius: 999px;
  padding: 2px 10px;
}
.trophy {
  font-size: 56px;
  line-height: 1.1;
}
.res-stars {
  flex: none;
  font-size: 14px;
}
@media (prefers-reduced-motion: reduce) {
  .win-stars i {
    animation: none;
  }
}
.ok {
  color: var(--ok);
}
.bad {
  color: var(--bad);
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
  .caret {
    animation: none;
  }
}
.hints {
  margin-top: 12px;
  display: grid;
  gap: 8px;
}
.hint {
  background: var(--warn-soft);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 15px;
}
.hint b {
  display: block;
  color: var(--warn-text);
  font-size: 13px;
}
.solution {
  margin-top: 12px;
}
.solution p {
  margin: 6px 0 0;
}
.ans-line strong {
  color: var(--ok);
  font-size: 18px;
}
.tools {
  display: flex;
  gap: 10px;
  margin: 14px 0;
}
.tools .btn {
  flex: 1;
}
.tip {
  font-size: 12px;
  margin: -6px 0 12px;
  text-align: center;
}
.keypad {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.key {
  min-height: 52px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: var(--card);
  font-size: 22px;
  font-weight: 600;
  box-shadow: var(--shadow);
}
.key:active {
  background: var(--primary-soft);
}
.key.fn {
  font-size: 20px;
}
.key.submit {
  grid-column: span 2;
  background: var(--primary);
  border-color: var(--primary);
  color: var(--on-primary);
  font-size: 18px;
}
.key.submit:disabled {
  opacity: 0.45;
}
.next {
  margin-top: 16px;
}
.wide {
  width: 100%;
  min-height: 50px;
  font-size: 17px;
}
.summary {
  text-align: center;
}
.score {
  font-size: 52px;
  font-weight: 800;
  color: var(--primary);
  line-height: 1.1;
}
.score small {
  font-size: 22px;
  color: var(--muted);
}
.praise {
  font-weight: 600;
}
.res-list {
  list-style: none;
  padding: 0;
  margin: 12px 0;
  text-align: left;
}
.res-list li {
  display: flex;
  gap: 10px;
  padding: 8px 0;
  border-top: 1px solid var(--line);
  font-size: 14px;
}
.res-list li > span:first-child {
  font-weight: 800;
  flex: none;
}
.res-stem {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}
.toast {
  position: fixed;
  left: 50%;
  bottom: 40px;
  transform: translateX(-50%);
  background: var(--text);
  color: var(--bg);
  padding: 10px 18px;
  border-radius: 999px;
  font-size: 14px;
  z-index: 20;
}
</style>
