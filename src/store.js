import { reactive, watch } from 'vue'
import { todayStr } from './bank.js'

const KEY = 'aoshu:v1'
const blank = () => ({
  grade: 0,
  records: {},
  wrong: {},
  daily: { last: '', streak: 0, done: [] },
  installTipClosed: false,
  sound: true,
  g24: { solved: 0, streak: 0, best: 0 },
  sudoku: { wins: 0, hard: false },
  slide: { wins3: 0, wins4: 0, best3: null, best4: null, size: 3 },
  pet: { owned: [], equip: null, food: 60, fedAt: Date.now(), spent: 0 },
})

const NESTED = ['daily', 'g24', 'sudoku', 'slide', 'pet']

function load() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || 'null')
    if (!saved) return blank()
    const b = blank()
    const merged = { ...b, ...saved }
    for (const k of NESTED) merged[k] = { ...b[k], ...saved[k] }
    return merged
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

// 3 = right first time without hints, 2 = needed hints or one retry, 1 = got there eventually, 0 = looked at the answer
export function starsFor({ status, attempts, hints }) {
  if (status !== 'correct') return 0
  if (attempts === 1 && hints === 0) return 3
  if (attempts <= 2) return 2
  return 1
}

export function recordStars(qid, stars) {
  const r = state.records[qid]
  if (r) r.stars = Math.max(r.stars ?? 0, stars)
}

export function starsOf(qid) {
  const r = state.records[qid]
  if (!r) return null
  if (r.stars != null) return r.stars
  if (r.correct > 0) return r.firstTry ? 3 : 1
  return 0
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
