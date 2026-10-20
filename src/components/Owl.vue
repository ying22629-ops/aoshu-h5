<script setup>
import { computed, ref } from 'vue'
import { itemById, stage } from '../rewards.js'
import { state } from '../store.js'

const props = defineProps({ size: { type: Number, default: 96 }, still: { type: Boolean, default: false } })
const emit = defineEmits(['poke'])

const SLOT = { bow: 'head', hat: 'head', grad: 'head', crown: 'head', glasses: 'face', scarf: 'neck' }
const item = computed(() => (state.pet.equip ? itemById(state.pet.equip) : null))
const slot = computed(() => (item.value ? SLOT[item.value.id] : null))
const px = computed(() => Math.round(props.size * stage.value.size))
const hop = ref(false)

function poke() {
  hop.value = false
  requestAnimationFrame(() => (hop.value = true))
  setTimeout(() => (hop.value = false), 500)
  emit('poke')
}
</script>

<template>
  <component
    :is="still ? 'span' : 'button'"
    class="owl"
    :class="{ hop }"
    :style="{ '--s': px + 'px' }"
    :aria-label="still ? undefined : `小智:${stage.name}`"
    @click="still || poke()"
  >
    <span class="body">{{ stage.emoji }}</span>
    <span v-if="item" class="acc" :class="slot" aria-hidden="true">{{ item.emoji }}</span>
  </component>
</template>

<style scoped>
.owl {
  display: inline-block;
  position: relative;
  width: var(--s);
  height: var(--s);
  border: none;
  background: none;
  padding: 0;
  line-height: 1;
  cursor: pointer;
}
.body {
  display: block;
  font-size: var(--s);
  line-height: 1;
}
.acc {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  font-size: calc(var(--s) * 0.42);
  line-height: 1;
}
.acc.head {
  top: calc(var(--s) * -0.26);
}
.acc.face {
  top: calc(var(--s) * 0.22);
  font-size: calc(var(--s) * 0.36);
}
.acc.neck {
  top: calc(var(--s) * 0.6);
  font-size: calc(var(--s) * 0.34);
}
.hop {
  animation: hop 0.45s;
}
@keyframes hop {
  40% {
    transform: translateY(-18%) rotate(-6deg);
  }
  70% {
    transform: translateY(0) rotate(4deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .hop {
    animation: none;
  }
}
</style>
