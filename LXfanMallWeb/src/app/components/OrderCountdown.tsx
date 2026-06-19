import { useState, useEffect, useCallback } from "react"
import { Clock, AlertCircle } from "lucide-react"

interface OrderCountdownProps {
  createTime: string
  timeoutMinutes?: number
  onExpired?: () => void
  className?: string
}

export function OrderCountdown({
  createTime,
  timeoutMinutes = 15,
  onExpired,
  className = "",
}: OrderCountdownProps) {
  const calculateRemaining = useCallback(() => {
    const created = new Date(createTime).getTime()
    const deadline = created + timeoutMinutes * 60 * 1000
    const remaining = deadline - Date.now()
    return remaining > 0 ? remaining : 0
  }, [createTime, timeoutMinutes])

  const [remaining, setRemaining] = useState(calculateRemaining)

  useEffect(() => {
    if (remaining <= 0) {
      onExpired?.()
      return
    }

    const timer = setInterval(() => {
      const newRemaining = calculateRemaining()
      setRemaining(newRemaining)
      if (newRemaining <= 0) {
        clearInterval(timer)
        onExpired?.()
      }
    }, 1000)

    return () => clearInterval(timer)
  }, [calculateRemaining, onExpired, remaining])

  if (remaining <= 0) {
    return (
      <div className={`flex items-center gap-1.5 text-red-500 ${className}`}>
        <AlertCircle size={14} />
        <span className="text-xs font-medium">支付已超时</span>
      </div>
    )
  }

  const totalSeconds = Math.floor(remaining / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60

  const isUrgent = minutes < 5

  return (
    <div
      className={`flex items-center gap-1.5 ${
        isUrgent ? "text-red-500" : "text-orange-500"
      } ${className}`}
    >
      <Clock size={14} className={isUrgent ? "animate-pulse" : ""} />
      <span className="text-xs font-medium">
        剩余支付时间: {String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
      </span>
    </div>
  )
}
