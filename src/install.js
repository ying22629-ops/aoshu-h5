import { ref } from 'vue'

const ua = navigator.userAgent
export const isWeChat = /MicroMessenger/i.test(ua)
export const isIOS = /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
export const isAndroid = /Android/i.test(ua)
export const isMobile = isIOS || isAndroid
export const isStandalone = ref(
  window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true,
)

const deferred = ref(null)
export const canPromptInstall = ref(false)

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault()
  deferred.value = e
  canPromptInstall.value = true
})
window.addEventListener('appinstalled', () => {
  canPromptInstall.value = false
  isStandalone.value = true
})

export async function promptInstall() {
  if (!deferred.value) return false
  deferred.value.prompt()
  const { outcome } = await deferred.value.userChoice
  deferred.value = null
  canPromptInstall.value = false
  return outcome === 'accepted'
}
