import { useState, useEffect } from "react"

export function useCountdown(targetMs: number) {
  const [remaining, setRemaining] = useState(() => Math.max(0, targetMs - Date.now()))

  useEffect(() => {
    if (remaining <= 0) return

    const timer = setInterval(() => {
      const left = Math.max(0, targetMs - Date.now())
      setRemaining(left)
      if (left <= 0) clearInterval(timer)
    }, 1000)

    return () => clearInterval(timer)
  }, [targetMs])

  const minutes = Math.floor(remaining / 60000)
  const seconds = Math.floor((remaining % 60000) / 1000)
  const expired = remaining <= 0

  return { minutes, seconds, expired, remaining }
}
