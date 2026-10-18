<script setup>
import { computed } from 'vue'

const svgs = import.meta.glob('../figures/*.svg', { query: '?raw', import: 'default', eager: true })
const props = defineProps({ name: { type: String, required: true }, label: { type: String, default: '题目配图' } })
const svg = computed(() => svgs[`../figures/${props.name}.svg`] ?? '')
</script>

<template>
  <figure v-if="svg" class="qfig" role="img" :aria-label="label" v-html="svg"></figure>
</template>

<style scoped>
.qfig {
  margin: 4px 0 14px;
  color: var(--text);
}
.qfig :deep(svg) {
  display: block;
  width: 100%;
  max-width: 320px;
  height: auto;
  max-height: 170px;
  margin: 0 auto;
  overflow: visible;
}
.qfig :deep(.l) {
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linejoin: round;
  stroke-linecap: round;
}
.qfig :deep(.d) {
  stroke-dasharray: 6 5;
}
.qfig :deep(.a) {
  stroke: var(--primary);
}
.qfig :deep(.s) {
  fill: var(--primary-soft);
}
.qfig :deep(.w) {
  fill: var(--warn-soft);
}
.qfig :deep(.f) {
  fill: currentColor;
  stroke: none;
}
.qfig :deep(.fa) {
  fill: var(--primary);
  stroke: none;
}
.qfig :deep(text) {
  fill: currentColor;
  font-size: 14px;
  text-anchor: middle;
  dominant-baseline: central;
}
.qfig :deep(text.ta) {
  fill: var(--primary);
  font-weight: 600;
}
.qfig :deep(text.sm) {
  font-size: 12px;
}
</style>
