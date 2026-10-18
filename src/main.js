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

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Home, meta: { tab: 'home' } },
    { path: '/practice/:mode/:id', component: Practice, props: true },
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
