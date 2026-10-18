<script setup>
import { computed, ref } from 'vue'
import { aiReady, hasBuiltInKey, localKey, saveLocalKey, testConnection } from '../ai.js'

const input = ref('')
const testing = ref(false)
const result = ref(null)

const status = computed(() => {
  if (localKey.value) return '已开启(使用本机填写的 key)'
  if (hasBuiltInKey) return '已开启(使用打包时配置的 key)'
  return '未开启'
})

function save() {
  saveLocalKey(input.value)
  input.value = ''
  result.value = null
}

function clear() {
  saveLocalKey('')
  result.value = null
}

async function test() {
  testing.value = true
  result.value = null
  try {
    await testConnection()
    result.value = { ok: true, text: '连接成功,AI 老师可以用了。' }
  } catch (e) {
    result.value = { ok: false, text: e.message }
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="ai-set">
    <p class="status">
      AI 讲解:<b :class="aiReady() ? 'on' : 'off'">{{ status }}</b>
    </p>
    <p class="muted desc">开启后,做题时可以让 AI 老师讲思路、分析错在哪,还能继续追问。由 DeepSeek 提供。</p>

    <form class="row" @submit.prevent="save">
      <input
        v-model="input"
        type="password"
        autocomplete="off"
        spellcheck="false"
        placeholder="粘贴 DeepSeek API key"
        aria-label="DeepSeek API key"
      />
      <button class="btn primary" :disabled="!input.trim()">保存</button>
    </form>
    <div class="row actions">
      <button class="btn soft" :disabled="!aiReady() || testing" @click="test">{{ testing ? '测试中…' : '测试连接' }}</button>
      <button v-if="localKey" class="btn" @click="clear">清除本机 key</button>
    </div>
    <p v-if="result" class="result" :class="result.ok ? 'on' : 'off'" role="status">{{ result.text }}</p>
    <p class="muted desc">key 只保存在这台设备的浏览器里。</p>
  </div>
</template>

<style scoped>
.ai-set {
  font-size: 14px;
}
.status,
.desc,
.result {
  margin: 0 0 8px;
}
.on {
  color: var(--ok);
}
.off {
  color: var(--bad);
}
.row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.row input {
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
.row input:focus-visible {
  outline: 3px solid var(--primary);
  outline-offset: 1px;
}
.actions .btn {
  flex: 1;
}
</style>
