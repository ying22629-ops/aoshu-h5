<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { state } from './store.js'

const route = useRoute()
const tab = computed(() => route.meta.tab)
const wrongCount = computed(() => Object.keys(state.wrong).length)
</script>

<template>
  <div class="shell">
    <main class="page" :class="{ 'has-tabs': tab }">
      <RouterView />
    </main>
    <nav v-if="tab" class="tabbar" aria-label="主导航">
      <RouterLink to="/" :class="{ on: tab === 'home' }">
        <span class="ico" aria-hidden="true">⌂</span>练习
      </RouterLink>
      <RouterLink to="/wrong" :class="{ on: tab === 'wrong' }">
        <span class="ico" aria-hidden="true">✎</span>错题本
        <b v-if="wrongCount" class="badge">{{ wrongCount }}</b>
      </RouterLink>
      <RouterLink to="/me" :class="{ on: tab === 'me' }">
        <span class="ico" aria-hidden="true">☺</span>我的
      </RouterLink>
    </nav>
  </div>
</template>
