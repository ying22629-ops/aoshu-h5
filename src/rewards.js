import { computed } from 'vue'
import { starsOf, state } from './store.js'

export const GAME_STARS = { g24: 1, sudoku: 2, slide3: 2, slide4: 3 }

export const questionStars = computed(() =>
  Object.keys(state.records).reduce((s, id) => s + (starsOf(id) ?? 0), 0),
)
export const gameStars = computed(
  () =>
    state.g24.solved * GAME_STARS.g24 +
    state.sudoku.wins * GAME_STARS.sudoku +
    state.slide.wins3 * GAME_STARS.slide3 +
    state.slide.wins4 * GAME_STARS.slide4,
)
export const earnedStars = computed(() => questionStars.value + gameStars.value)
export const balance = computed(() => Math.max(0, earnedStars.value - state.pet.spent))

export const STAGES = [
  { min: 0, name: '神秘的蛋', emoji: '🥚', size: 0.8, line: '多做几道题,我就要孵出来啦!' },
  { min: 5, name: '破壳小智', emoji: '🐣', size: 0.9, line: '我出来啦!再多给我一些星星吧~' },
  { min: 15, name: '小猫头鹰', emoji: '🦉', size: 0.9, line: '我会飞一点点了!' },
  { min: 40, name: '机灵猫头鹰', emoji: '🦉', size: 1.1, line: '我们一起挑战更难的题吧!' },
  { min: 80, name: '智慧猫头鹰', emoji: '🦉', size: 1.25, line: '你真是数学小天才!' },
]

export const stage = computed(() => {
  let s = STAGES[0]
  for (const st of STAGES) if (earnedStars.value >= st.min) s = st
  return s
})
export const nextStage = computed(() => STAGES.find((s) => s.min > earnedStars.value) ?? null)

export const ITEMS = [
  { id: 'bow', emoji: '🎀', name: '蝴蝶结', cost: 5 },
  { id: 'scarf', emoji: '🧣', name: '围巾', cost: 8 },
  { id: 'hat', emoji: '🎩', name: '小礼帽', cost: 12 },
  { id: 'glasses', emoji: '👓', name: '眼镜', cost: 15 },
  { id: 'grad', emoji: '🎓', name: '博士帽', cost: 25 },
  { id: 'crown', emoji: '👑', name: '皇冠', cost: 40 },
]
export const itemById = (id) => ITEMS.find((i) => i.id === id)

const FOOD_PER_DAY = 25
const DAY = 24 * 3600 * 1000

export const food = computed(() => {
  const days = (Date.now() - state.pet.fedAt) / DAY
  return Math.max(0, Math.round(state.pet.food - days * FOOD_PER_DAY))
})

export function feed() {
  if (balance.value < 1 || food.value >= 100) return false
  state.pet.food = Math.min(100, food.value + 25)
  state.pet.fedAt = Date.now()
  state.pet.spent += 1
  return true
}

export function buy(id) {
  const item = itemById(id)
  if (!item || state.pet.owned.includes(id) || balance.value < item.cost) return false
  state.pet.spent += item.cost
  state.pet.owned.push(id)
  state.pet.equip = id
  return true
}

export function equip(id) {
  if (id === null || state.pet.owned.includes(id)) state.pet.equip = id
}
