import { reactive, watch } from 'vue'
import { todayStr } from './bank.js'

const KEY = 'aoshu:v1'
const blank = () => ({ grade: 0, records: {}, wrong: {}, daily: { last: '', streak: 0, done: [] } })

function load() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || 'null')
    return saved ? { ...blank(), ...saved, daily: { ...blank().daily, ...saved.daily } } : blank()
  } catch {
    return blank()
  }
}

export const state = reactive(load())

watch(
  state,
  (s) => {
    try {
      localStorage.setItem(KEY, JSON.stringify(s))
    } catch {
      /* storage unavailable (private mode); progress lasts this session only */
    }
  },
  { deep: true },
)

export function recordAttempt(qid, correct, { hintsUsed = 0, review = false } = {}) {
  const r = (state.records[qid] ||= { attempts: 0, correct: 0, firstTry: null, hintsMax: 0 })
  r.attempts += 1
  if (correct) r.correct += 1
  if (r.firstTry === null) r.firstTry = correct && hintsUsed === 0
  r.hintsMax = Math.max(r.hintsMax, hintsUsed)

  if (review && state.wrong[qid]) state.wrong[qid].reviews += 1
  if (!correct && !state.wrong[qid]) state.wrong[qid] = { addedAt: Date.now(), reviews: 0 }
  if (correct && review && state.wrong[qid]) {
    delete state.wrong[qid]
    return { mastered: true }
  }
  return { mastered: false }
}

export function markGaveUp(qid) {
  const r = (state.records[qid] ||= { attempts: 0, correct: 0, firstTry: null, hintsMax: 0 })
  if (r.firstTry === null) r.firstTry = false
  if (!state.wrong[qid]) state.wrong[qid] = { addedAt: Date.now(), reviews: 0 }
}

export function finishDaily() {
  const today = todayStr()
  const d = state.daily
  if (d.last === today) return
  const y = new Date()
  y.setDate(y.getDate() - 1)
  d.streak = d.last === todayStr(y) ? d.streak + 1 : 1
  d.last = today
  d.done = [...d.done.slice(-59), today]
}

export function currentStreak() {
  const d = state.daily
  const y = new Date()
  y.setDate(y.getDate() - 1)
  return d.last === todayStr() || d.last === todayStr(y) ? d.streak : 0
}

export function resetAll() {
  Object.assign(state, blank())
}
