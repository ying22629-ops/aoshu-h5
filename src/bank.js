import bank from './data/questions.json'

export const topics = bank.topics
export const questions = bank.questions
const byId = new Map(questions.map((q) => [q.id, q]))

export const getQuestion = (id) => byId.get(id)
export const getTopic = (id) => topics.find((t) => t.id === id)

export function questionsFor(topicId, grade) {
  return questions
    .filter((q) => q.topic === topicId && (!grade || q.grade <= grade))
    .sort((a, b) => a.difficulty - b.difficulty || a.grade - b.grade)
}

export function todayStr(d = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function dailyQuestion(dateStr, grade) {
  const pool = grade ? questions.filter((q) => q.grade <= grade) : questions
  let h = 0
  for (const ch of dateStr) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return pool[h % pool.length]
}

const FULLWIDTH = /[！-～]/g

function toNumber(s) {
  const frac = s.match(/^(-?\d+(?:\.\d+)?)\/(\d+(?:\.\d+)?)$/)
  if (frac) return Number(frac[2]) === 0 ? NaN : Number(frac[1]) / Number(frac[2])
  return /^-?\d+(?:\.\d+)?$/.test(s) ? Number(s) : NaN
}

export function normalizeAnswer(raw) {
  return String(raw)
    .replace(FULLWIDTH, (c) => String.fromCharCode(c.charCodeAt(0) - 0xfee0))
    .replace(/[÷]/g, '/')
    .replace(/\s+/g, '')
    .replace(/[一-龥°]+$/, '')
}

export function isCorrect(q, raw) {
  if (q.type === 'choice') return raw === q.answer
  const given = normalizeAnswer(raw)
  if (!given) return false
  if (given === q.answer) return true
  const a = toNumber(given)
  const b = toNumber(q.answer)
  return !Number.isNaN(a) && !Number.isNaN(b) && Math.abs(a - b) < 1e-9
}
