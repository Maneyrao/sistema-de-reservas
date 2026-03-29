import { cn } from "@/lib/utils"

type BrandLoaderProps = {
  message?: string
  fullscreen?: boolean
  className?: string
}

export function BrandLoader({
  message = "Cargando experiencia Club Amsterdam...",
  fullscreen = true,
  className,
}: BrandLoaderProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-center bg-zinc-950 text-zinc-50",
        fullscreen ? "min-h-screen" : "min-h-[320px]",
        className,
      )}
    >
      <div className="text-center">
        <div className="club-loader-shell mx-auto">
          <div className="club-loader-glow" />
          <img
            src="/club-amsterdam-monogram.svg"
            alt="Club Amsterdam"
            className="club-loader-mark"
          />
        </div>
        <p className="mt-6 text-xs uppercase tracking-[0.45em] text-amber-500/80">
          Club Amsterdam
        </p>
        <p className="mt-2 text-sm text-zinc-400">{message}</p>
      </div>
    </div>
  )
}
