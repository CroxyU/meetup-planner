/** Обёртка над Telegram WebApp SDK. */
import { onMounted, ref } from 'vue'

export function useTelegram() {
  const tg = ref(null)
  const theme = ref('light')

  onMounted(() => {
    const w = window.Telegram?.WebApp
    if (w) {
      w.ready()
      w.expand()
      tg.value = w
      theme.value = w.colorScheme || 'light'
      applyTheme(w)
      w.onEvent('themeChanged', () => applyTheme(w))
    }
  })

  function applyTheme(w) {
    const root = document.documentElement
    const p = w.themeParams || {}
    root.style.setProperty('--tg-bg', p.bg_color || '#ffffff')
    root.style.setProperty('--tg-text', p.text_color || '#000000')
    root.style.setProperty('--tg-hint', p.hint_color || '#999999')
    root.style.setProperty('--tg-link', p.link_color || '#2481cc')
    root.style.setProperty('--tg-button', p.button_color || '#2481cc')
    root.style.setProperty('--tg-button-text', p.button_text_color || '#ffffff')
    root.style.setProperty('--tg-secondary-bg', p.secondary_bg_color || '#f4f4f5')
    root.dataset.theme = w.colorScheme
  }

  function haptic(type = 'light') {
    tg.value?.HapticFeedback?.impactOccurred(type)
  }

  return { tg, theme, haptic }
}
