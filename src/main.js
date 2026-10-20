import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import 'katex/dist/katex.min.css'
import './style.css'
import './install.js'
import App from './App.vue'
import Home from './views/Home.vue'
import Practice from './views/Practice.vue'
import WrongBook from './views/WrongBook.vue'
import Me from './views/Me.vue'
import MapView from './views/Map.vue'
import Game24 from './views/Game24.vue'
import Sudoku from './views/Sudoku.vue'
import Slide from './views/Slide.vue'
import Pet from './views/Pet.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Home, meta: { tab: 'home' } },
    { path: '/practice/:mode/:id', component: Practice, props: true },
    { path: '/map/:topic', component: MapView, props: true },
    { path: '/game/24', component: Game24 },
    { path: '/game/sudoku', component: Sudoku },
    { path: '/game/slide', component: Slide },
    { path: '/pet', component: Pet },
    { path: '/wrong', component: WrongBook, meta: { tab: 'wrong' } },
    { path: '/me', component: Me, meta: { tab: 'me' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

createApp(App).use(router).mount('#app')

if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('./sw.js').catch(() => {}))
}
