export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-[#D2D2D7]/60 bg-white/90 backdrop-blur-xl">
      <div className="mx-auto max-w-5xl px-6 py-4 flex items-center justify-between">
        <span className="text-[17px] font-semibold tracking-tight text-[#1D1D1F]">
          Eventra
        </span>
        <span className="text-xs text-[#86868B] font-medium tracking-wide uppercase">
          AI Event Planner
        </span>
      </div>
    </header>
  )
}
