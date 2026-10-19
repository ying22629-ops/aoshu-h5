import { state } from './store.js'

let ctx = null

function audio() {
  if (!state.sound) return null
  try {
    ctx ||= new (window.AudioContext || window.webkitAudioContext)()
    if (ctx.state === 'suspended') ctx.resume()
    return ctx
  } catch {
    return null
  }
}

function tone(freq, start, dur, { type = 'sine', gain = 0.18 } = {}) {
  const ac = audio()
  if (!ac) return
  const t = ac.currentTime + start
  const osc = ac.createOscillator()
  const g = ac.createGain()
  osc.type = type
  osc.frequency.setValueAtTime(freq, t)
  g.gain.setValueAtTime(0.0001, t)
  g.gain.exponentialRampToValueAtTime(gain, t + 0.02)
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur)
  osc.connect(g).connect(ac.destination)
  osc.start(t)
  osc.stop(t + dur + 0.05)
}

export const sfx = {
  correct() {
    tone(523, 0, 0.15)
    tone(659, 0.09, 0.15)
    tone(784, 0.18, 0.28)
  },
  wrong() {
    tone(330, 0, 0.16, { type: 'triangle', gain: 0.14 })
    tone(262, 0.12, 0.24, { type: 'triangle', gain: 0.12 })
  },
  star(i) {
    tone(880 + i * 220, 0, 0.22, { gain: 0.12 })
  },
  tap() {
    tone(660, 0, 0.06, { type: 'triangle', gain: 0.06 })
  },
  win() {
    ;[523, 659, 784, 1047].forEach((f, i) => tone(f, i * 0.1, 0.25))
    tone(1319, 0.42, 0.45, { gain: 0.14 })
  },
}
