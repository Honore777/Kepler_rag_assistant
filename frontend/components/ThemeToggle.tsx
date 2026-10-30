import { toggleTheme } from '../lib/theme'
import { MoonIcon, SunIcon } from './icons'

/**
 * Icon swap is pure CSS (driven by [data-theme]) so the server markup never
 * disagrees with the client and there is no icon flash.
 */
export default function ThemeToggle({ className = '' }: { className?: string }) {
  return (
    <button
      type="button"
      onClick={() => toggleTheme()}
      className={`inline-flex h-10 w-10 items-center justify-center rounded-xl border border-line text-ink-soft transition-colors hover:bg-raised hover:text-ink ${className}`}
      aria-label="Switch between light and dark mode"
      title="Switch between light and dark mode"
    >
      <MoonIcon className="theme-show-light h-[18px] w-[18px]" />
      <SunIcon className="theme-show-dark h-[18px] w-[18px]" />
    </button>
  )
}
