const COLORS = ['#6366f1', '#f59e0b', '#ec4899', '#10b981', '#3b82f6', '#f43f5e', '#facc15']

export function confetti(count = 36) {
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
  const layer = document.createElement('div')
  layer.setAttribute('aria-hidden', 'true')
  layer.style.cssText = 'position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:50'
  for (let i = 0; i < count; i++) {
    const p = document.createElement('i')
    const size = 6 + Math.random() * 6
    const dx = (Math.random() - 0.5) * 320
    const dy = 280 + Math.random() * 320
    const rot = (Math.random() - 0.5) * 900
    p.style.cssText = `position:absolute;left:50%;top:38%;width:${size}px;height:${size * 0.5}px;background:${COLORS[i % COLORS.length]};border-radius:2px;`
    p.animate(
      [
        { transform: 'translate(-50%,0) rotate(0deg)', opacity: 1 },
        { transform: `translate(calc(-50% + ${dx * 0.6}px), -${120 + Math.random() * 120}px) rotate(${rot / 2}deg)`, opacity: 1, offset: 0.35 },
        { transform: `translate(calc(-50% + ${dx}px), ${dy}px) rotate(${rot}deg)`, opacity: 0 },
      ],
      { duration: 1100 + Math.random() * 500, easing: 'cubic-bezier(.2,.7,.4,1)', fill: 'forwards' },
    )
    layer.appendChild(p)
  }
  document.body.appendChild(layer)
  setTimeout(() => layer.remove(), 1800)
}
