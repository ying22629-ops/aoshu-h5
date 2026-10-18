import { ref } from 'vue'

const KEY_STORE = 'aoshu:aiKey'
const BASE = (import.meta.env.VITE_AI_BASE_URL || 'https://api.deepseek.com').replace(/\/$/, '')
const MODEL = import.meta.env.VITE_AI_MODEL || 'deepseek-chat'
const BUILT_IN_KEY = import.meta.env.VITE_DEEPSEEK_API_KEY || ''
export const MAX_TURNS = 6

function readLocalKey() {
  try {
    return localStorage.getItem(KEY_STORE) || ''
  } catch {
    return ''
  }
}

export const localKey = ref(readLocalKey())
export const hasBuiltInKey = Boolean(BUILT_IN_KEY)
export const aiReady = () => Boolean(localKey.value || BUILT_IN_KEY)

export function saveLocalKey(k) {
  localKey.value = k.trim()
  try {
    if (localKey.value) localStorage.setItem(KEY_STORE, localKey.value)
    else localStorage.removeItem(KEY_STORE)
  } catch {
    /* storage unavailable: key lasts this session only */
  }
}

export function systemPrompt(q, { revealed, wrongAnswers }) {
  const tried = wrongAnswers.length ? `孩子之前答错过:${wrongAnswers.join('、')}。` : '孩子还没有作答。'
  const mode = revealed
    ? '孩子已经看到或做出了正确答案,可以完整讲解。'
    : '孩子还没做出来:只引导思路,一步一步提问启发,绝对不要说出最终答案。'
  return [
    `你是一位耐心、亲切的小学数学老师,正在给${q.grade}年级的孩子讲一道思维题。`,
    '规则:',
    '- 用孩子听得懂的话,句子短,每次回答不超过 150 字,可以分 2~4 小步。',
    '- 数学式子用 $...$ 包起来,不要用 \\( \\) 或 \\[ \\],不要用 Markdown 标题、表格和加粗。',
    '- 如果孩子答错了,先猜一猜孩子是怎么想的、错在哪一步,再引导孩子自己改正。',
    '- 只讨论这道题和相关的数学知识;孩子问别的,就温柔地把话题拉回来。',
    '- 不要询问或提到孩子的姓名、学校等个人信息。多鼓励,不批评。',
    `- ${mode}`,
    '',
    `题目:${q.stem}`,
    q.options ? `选项:${q.options.join(' / ')}` : '',
    `标准答案:${q.answer}`,
    `参考解析:${q.solution}`,
    tried,
  ]
    .filter(Boolean)
    .join('\n')
}

export function tidyAiText(s) {
  return s
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, m) => `$$${m}$$`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, m) => `$${m}$`)
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/^#+\s*/gm, '')
}

const ERRORS = {
  401: 'AI 的 key 无效,请到“我的”页面检查设置。',
  402: 'AI 账户余额不足,请充值后再试。',
  429: '问得太快啦,稍等几秒再试。',
}

export async function streamChat(messages, onDelta, signal) {
  const key = localKey.value || BUILT_IN_KEY
  if (!key) throw new Error('还没有设置 AI 的 key。')
  let res
  try {
    res = await fetch(`${BASE}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${key}` },
      body: JSON.stringify({ model: MODEL, messages, stream: true, temperature: 0.3, max_tokens: 500 }),
      signal,
    })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new Error('网络连接失败,请检查网络后再试。')
  }
  if (!res.ok) throw new Error(ERRORS[res.status] || `AI 服务暂时不可用(${res.status}),请稍后再试。`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  let full = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const lines = buf.split('\n')
    buf = lines.pop()
    for (const line of lines) {
      const data = line.trim().replace(/^data:\s*/, '')
      if (!data || data === '[DONE]' || !line.trim().startsWith('data:')) continue
      try {
        const delta = JSON.parse(data).choices?.[0]?.delta?.content
        if (delta) {
          full += delta
          onDelta(full)
        }
      } catch {
        /* keep-alive or partial line */
      }
    }
  }
  return full
}

export async function testConnection() {
  await streamChat([{ role: 'user', content: '只回复两个字:你好' }], () => {})
}
