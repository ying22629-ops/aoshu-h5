<script setup>
import { computed } from 'vue'
import katex from 'katex'

const props = defineProps({ text: { type: String, required: true } })

const escape = (s) =>
  s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])

const html = computed(() =>
  props.text
    .split(/(\$\$[^$]+\$\$|\$[^$]+\$)/g)
    .map((part) => {
      const display = part.startsWith('$$')
      if (part.length > 1 && part.startsWith('$') && part.endsWith('$')) {
        const tex = display ? part.slice(2, -2) : part.slice(1, -1)
        return katex.renderToString(tex, { displayMode: display, throwOnError: false })
      }
      return escape(part).replace(/\n/g, '<br>')
    })
    .join(''),
)
</script>

<template>
  <span class="math-text" v-html="html"></span>
</template>

<style scoped>
.math-text :deep(.katex) {
  font-size: 1.08em;
}
.math-text :deep(.katex-display) {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 4px 0;
}
</style>
