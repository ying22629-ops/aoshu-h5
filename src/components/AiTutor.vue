<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import MathText from './MathText.vue'
import { MAX_TURNS, streamChat, systemPrompt, tidyAiText } from '../ai.js'

const props = defineProps({
  q: { type: Object, required: true },
  status: { type: String, required: true },
  wrongAnswers: { type: Array, required: true },
})

const open = ref(false)
const chat = ref([])
const streaming = ref('')
const busy = ref(false)
const error = ref('')
const draft = ref('')
const listEl = ref(null)
let ctrl = null

const revealed = computed(() => props.status === 'correct' || props.status === 'revealed')
const turns = computed(() => chat.value.filter((m) => m.role === 'user').length)
const outOfTurns = computed(() => turns.value >= MAX_TURNS)

const starter = computed(() => {
  if (props.status === 'correct') return { label: '🤖 让 AI 老师再讲讲', text: '我做对了,能再给我讲讲为什么这样做吗?' }
  if (props.status === 'revealed') return { label: '🤖 看不懂解析?问 AI 老师', text: '解析我没看懂,能讲得再简单一点吗?' }
  if (props.wrongAnswers.length) {
    const last = props.wrongAnswers[props.wrongAnswers.length - 1]
    return { label: '🤖 AI 老师帮我看看错在哪', text: `我答的是 ${last},为什么不对?` }
  }
  return { label: '🤖 不会做?问 AI 老师', text: '这道题我不会,能给我讲讲思路吗?' }
})

const quick = ['还是不懂', '换一种方法讲', '举个简单的例子']

async function scrollDown() {
  await nextTick()
  listEl.value?.scrollTo?.({ top: listEl.value.scrollHeight, behavior: 'smooth' })
}

async function ask(text) {
  const content = text.trim()
  if (!content || busy.value || outOfTurns.value) return
  open.value = true
  error.value = ''
  chat.value.push({ role: 'user', content })
  draft.value = ''
  busy.value = true
  streaming.value = ''
  scrollDown()
  ctrl = new AbortController()
  const messages = [
    { role: 'system', content: systemPrompt(props.q, { revealed: revealed.value, wrongAnswers: props.wrongAnswers }) },
    ...chat.value,
  ]
  try {
    const full = await streamChat(
      messages,
      (t) => {
        streaming.value = t
        scrollDown()
      },
      ctrl.signal,
    )
    chat.value.push({ role: 'assistant', content: full || '(AI 老师没有回答,再问一次试试)' })
  } catch (e) {
    if (e.name !== 'AbortError') {
      error.value = e.message
      chat.value.pop()
    }
  } finally {
    busy.value = false
    streaming.value = ''
    ctrl = null
    scrollDown()
  }
}

onBeforeUnmount(() => ctrl?.abort())
</script>

<template>
  <section class="tutor">
    <button v-if="!open" class="btn soft start" @click="ask(starter.text)">{{ starter.label }}</button>

    <div v-else class="card panel">
      <div class="head">
        <b>🤖 AI 老师</b>
        <button class="fold" @click="open = false">收起</button>
      </div>
      <div ref="listEl" class="list" aria-live="polite">
        <div v-for="(m, i) in chat" :key="i" class="msg" :class="m.role">
          <MathText v-if="m.role === 'assistant'" :text="tidyAiText(m.content)" />
          <template v-else>{{ m.content }}</template>
        </div>
        <div v-if="busy" class="msg assistant">
          <MathText v-if="streaming" :text="tidyAiText(streaming)" />
          <span v-else class="dots" aria-label="AI 老师正在思考">思考中<i>.</i><i>.</i><i>.</i></span>
        </div>
      </div>
      <p v-if="error" class="err" role="alert">{{ error }}</p>

      <template v-if="!outOfTurns">
        <div class="quick">
          <button v-for="t in quick" :key="t" class="chip" :disabled="busy" @click="ask(t)">{{ t }}</button>
        </div>
        <form class="ask" @submit.prevent="ask(draft)">
          <input
            v-model="draft"
            maxlength="100"
            placeholder="还有什么想问的?"
            aria-label="向 AI 老师提问"
            :disabled="busy"
            @keydown.stop
          />
          <button class="btn primary" :disabled="busy || !draft.trim()">问</button>
        </form>
      </template>
      <p v-else class="muted limit">这道题已经问了 {{ MAX_TURNS }} 次啦,自己再想一想,或者去下一题吧!</p>
      <p class="muted note">AI 回答仅供参考,可能出错。</p>
    </div>
  </section>
</template>

<style scoped>
.tutor {
  margin-top: 12px;
}
.start {
  width: 100%;
}
.panel {
  padding: 12px;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.fold {
  border: none;
  background: none;
  color: var(--muted);
  font-size: 13px;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 46vh;
  overflow-y: auto;
}
.msg {
  max-width: 88%;
  padding: 8px 12px;
  border-radius: 14px;
  font-size: 15px;
  line-height: 1.7;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.msg.user {
  align-self: flex-end;
  background: var(--primary);
  color: var(--on-primary);
  border-bottom-right-radius: 4px;
}
.msg.assistant {
  align-self: flex-start;
  background: var(--primary-soft);
  border-bottom-left-radius: 4px;
}
.dots i {
  font-style: normal;
  animation: blink 1.2s infinite;
}
.dots i:nth-child(2) {
  animation-delay: 0.2s;
}
.dots i:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  50% {
    opacity: 0.2;
  }
}
@media (prefers-reduced-motion: reduce) {
  .dots i {
    animation: none;
  }
}
.err {
  color: var(--bad);
  font-size: 14px;
  margin: 8px 0 0;
}
.quick {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
.ask {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.ask input {
  flex: 1;
  min-width: 0;
  min-height: 44px;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0 12px;
  font: inherit;
  font-size: 16px;
  background: var(--card);
  color: var(--text);
}
.ask input:focus-visible {
  outline: 3px solid var(--primary);
  outline-offset: 1px;
}
.limit,
.note {
  font-size: 12px;
  margin: 8px 0 0;
}
</style>
