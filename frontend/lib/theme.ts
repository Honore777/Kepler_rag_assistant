export type ThemeMode = 'dark' | 'light'

const THEME_STORAGE_KEY = 'rag-theme'

/** The visitor's saved choice; light unless they have switched to dark. */
export const getStoredTheme = (): ThemeMode => {
  if (typeof window === 'undefined') {
    return 'light'
  }

  return window.localStorage.getItem(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'light'
}

export const applyTheme = (theme: ThemeMode) => {
  if (typeof document === 'undefined') {
    return
  }

  document.documentElement.setAttribute('data-theme', theme)
  document.documentElement.style.colorScheme = theme

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme)
    window.dispatchEvent(new CustomEvent('rag-theme-change', { detail: theme }))
  }
}

export const initializeTheme = () => {
  if (typeof document === 'undefined') return
  // The inline script in _document.tsx has already set data-theme; just keep it in sync.
  document.documentElement.setAttribute('data-theme', getStoredTheme())
}

export const toggleTheme = (): ThemeMode => {
  const current =
    typeof document !== 'undefined' ? document.documentElement.getAttribute('data-theme') : null
  const nextTheme: ThemeMode = (current ?? getStoredTheme()) === 'dark' ? 'light' : 'dark'
  applyTheme(nextTheme)
  return nextTheme
}
