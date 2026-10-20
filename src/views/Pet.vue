<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import Owl from '../components/Owl.vue'
import { ITEMS, GAME_STARS, balance, buy, earnedStars, equip, feed, food, nextStage, stage } from '../rewards.js'
import { state } from '../store.js'
import { sfx } from '../sfx.js'
import { confetti } from '../confetti.js'

const router = useRouter()
const said = ref('')
const hearts = ref([])
let heartId = 0

const POKES = ['嘿嘿,好痒!', '今天想做什么题?', '我最喜欢 24 点了!', '一起动动脑吧!', '你今天真棒!']
const line = computed(() => {
  if (said.value) return said.value
  if (food.value < 30) return '我饿了……喂我一颗星星吧~'
  return stage.value.line
})
const progress = computed(() => {
  if (!nextStage.value) return 1
  const from = stage.value.min
  return (earnedStars.value - from) / (nextStage.value.min - from)
})

function say(text) {
  said.value = text
  setTimeout(() => (said.value = ''), 2500)
}

function poke() {
  sfx.tap()
  say(POKES[Math.floor(Math.random() * POKES.length)])
}

function doFeed() {
  if (food.value >= 100) return say('我已经吃饱啦!')
  if (!feed()) return say('星星不够了,去做题赚星星吧!')
  sfx.star(1)
  const id = ++heartId
  hearts.value.push(id)
  setTimeout(() => (hearts.value = hearts.value.filter((h) => h !== id)), 1300)
  say(food.value >= 100 ? '吃得饱饱的,谢谢你!' : '好吃!谢谢你~')
}

function doBuy(item) {
  if (state.pet.owned.includes(item.id)) {
    equip(state.pet.equip === item.id ? null : item.id)
    sfx.tap()
    return
  }
  if (!buy(item.id)) return say(`还差 ${item.cost - balance.value} 颗星星哦`)
  sfx.win()
  confetti(30)
  say(`哇,${item.name}!我好喜欢!`)
}

function back() {
  if (window.history.state?.back) router.back()
  else router.push('/')
}
</script>

<template>
  <header class="bar-top">
    <button class="icon-btn" aria-label="返回" @click="back">‹</button>
    <span class="ttl">我的小智</span>
    <span class="wallet" :aria-label="`可用 ${balance} 颗星`">⭐ {{ balance }}</span>
  </header>

  <section class="card stage">
    <p class="bubble" role="status">{{ line }}</p>
    <div class="owl-wrap">
      <Owl :size="128" @poke="poke" />
      <span v-for="h in hearts" :key="h" class="heart" aria-hidden="true">❤️</span>
    </div>
    <p class="name">{{ stage.name }}</p>
    <div class="grow">
      <span class="bar" aria-hidden="true"><i :style="{ width: progress * 100 + '%' }"></i></span>
      <span class="muted small">
        {{ nextStage ? `再得 ${nextStage.min - earnedStars} 颗星,就能变成「${nextStage.name}」` : '已经长到最大啦!' }}
      </span>
    </div>
  </section>

  <section class="card feed">
    <div class="feed-row">
      <span class="label">🍎 饱饱度</span>
      <span class="meter" role="meter" :aria-valuenow="food" aria-valuemin="0" aria-valuemax="100" aria-label="饱饱度">
        <i :class="{ low: food < 30 }" :style="{ width: food + '%' }"></i>
      </span>
      <span class="num">{{ food }}</span>
    </div>
    <button class="btn primary wide" :disabled="food >= 100" @click="doFeed">
      {{ food >= 100 ? '已经吃饱啦' : '喂一颗星星 (−1⭐)' }}
    </button>
    <p class="muted small">小智每天会饿一点,记得常回来看看它。</p>
  </section>

  <h2 class="section">装扮小店</h2>
  <div class="shop">
    <button
      v-for="it in ITEMS"
      :key="it.id"
      class="card item"
      :class="{ owned: state.pet.owned.includes(it.id), on: state.pet.equip === it.id }"
      :aria-pressed="state.pet.equip === it.id"
      @click="doBuy(it)"
    >
      <span class="it-emoji" aria-hidden="true">{{ it.emoji }}</span>
      <span class="it-name">{{ it.name }}</span>
      <span class="it-act">
        <template v-if="state.pet.equip === it.id">已戴上</template>
        <template v-else-if="state.pet.owned.includes(it.id)">戴上</template>
        <template v-else>⭐ {{ it.cost }}</template>
      </span>
    </button>
  </div>

  <h2 class="section">怎么得星星?</h2>
  <div class="card tips">
    <p>📘 闯关做题:一次做对、不看提示得 3 颗星</p>
    <p>🃏 24 点:每解出一题 +{{ GAME_STARS.g24 }}</p>
    <p>🔢 数独:每完成一盘 +{{ GAME_STARS.sudoku }}</p>
    <p>🧩 华容道:3×3 +{{ GAME_STARS.slide3 }},4×4 +{{ GAME_STARS.slide4 }}</p>
    <p class="muted small">累计获得 {{ earnedStars }} 颗,已经花掉 {{ state.pet.spent }} 颗。</p>
  </div>
</template>

<style scoped>
.bar-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: -4px 0 10px;
}
.icon-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  font-size: 30px;
  line-height: 1;
  margin-left: -8px;
}
.ttl {
  font-weight: 800;
  font-size: 20px;
  flex: 1;
}
.wallet {
  font-weight: 800;
  background: var(--warn-soft);
  color: var(--warn-text);
  border-radius: 999px;
  padding: 2px 12px;
}
.stage {
  text-align: center;
  background: linear-gradient(180deg, var(--primary-soft), var(--card));
}
.bubble {
  display: inline-block;
  position: relative;
  margin: 0 0 12px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 8px 14px;
  font-weight: 600;
  max-width: 90%;
}
.bubble::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -7px;
  width: 12px;
  height: 12px;
  background: var(--card);
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  transform: translateX(-50%) rotate(45deg);
}
.owl-wrap {
  position: relative;
  display: flex;
  justify-content: center;
  padding-top: 26px;
  min-height: 170px;
  align-items: flex-end;
}
.heart {
  position: absolute;
  left: 50%;
  top: 40%;
  font-size: 24px;
  animation: rise 1.2s forwards;
  pointer-events: none;
}
@keyframes rise {
  to {
    transform: translate(-50%, -90px) scale(1.4);
    opacity: 0;
  }
}
.name {
  font-weight: 800;
  font-size: 18px;
  margin: 8px 0 6px;
}
.grow {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.bar,
.meter {
  display: block;
  height: 10px;
  border-radius: 5px;
  background: var(--line);
  overflow: hidden;
}
.bar i,
.meter i {
  display: block;
  height: 100%;
  border-radius: 5px;
  background: linear-gradient(90deg, #facc15, #f59e0b);
  transition: width 0.4s;
}
.meter i.low {
  background: var(--bad);
}
.small {
  font-size: 12px;
  margin: 6px 0 0;
}
.feed {
  margin-top: 12px;
}
.feed-row {
  display: grid;
  grid-template-columns: auto 1fr 2.2em;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  font-weight: 600;
}
.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.wide {
  width: 100%;
}
.section {
  font-size: 18px;
  margin: 22px 0 10px;
}
.shop {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 12px 6px;
  font: inherit;
  color: inherit;
}
.item.on {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary);
}
.it-emoji {
  font-size: 34px;
  line-height: 1.1;
}
.it-name {
  font-size: 13px;
  font-weight: 700;
}
.it-act {
  font-size: 12px;
  font-weight: 700;
  color: var(--warn-text);
}
.item.owned .it-act {
  color: var(--primary);
}
.tips p {
  margin: 0 0 6px;
  font-size: 14px;
}
@media (prefers-reduced-motion: reduce) {
  .heart {
    animation: none;
    display: none;
  }
}
</style>
