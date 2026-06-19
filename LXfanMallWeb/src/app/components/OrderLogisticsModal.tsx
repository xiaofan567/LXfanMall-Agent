import { useState, useEffect } from "react"
import { orderApi } from "@/utils/api"
import { X, Truck, Circle, CheckCircle2, MapPin, Package, Loader2 } from "lucide-react"

interface TraceItem {
  traceTime: string
  location: string
  statusText: string
  statusCode: number
}

interface LogisticsData {
  deliveryCompany: string
  deliverySn: string
  deliveryTime: string
  receiverName: string
  receiverPhone: string
  receiverAddress: string
  traceList: TraceItem[]
}

interface Props {
  orderId: number
  open: boolean
  onClose: () => void
}

export function OrderLogisticsModal({ orderId, open, onClose }: Props) {
  const [data, setData] = useState<LogisticsData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (open && orderId) {
      setLoading(true)
      setError("")
      orderApi
        .getLogistics(orderId)
        .then((res: any) => setData(res))
        .catch(() => setError("获取物流信息失败"))
        .finally(() => setLoading(false))
    }
  }, [open, orderId])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] flex flex-col overflow-hidden mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
          <div className="flex items-center gap-2">
            <Package size={20} className="text-[#e02020]" />
            <h2 className="text-lg font-bold text-gray-900">物流详情</h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors"
          >
            <X size={18} className="text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex justify-center py-16">
              <Loader2 className="animate-spin text-[#e02020]" size={32} />
            </div>
          ) : error ? (
            <div className="text-center py-16 text-gray-400">{error}</div>
          ) : data ? (
            <>
              {/* Logistics Info */}
              <div className="bg-gray-50 rounded-xl p-4 mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <Truck size={16} className="text-gray-500" />
                  <span className="font-medium text-gray-800">{data.deliveryCompany}</span>
                  <span className="text-sm text-gray-500">{data.deliverySn}</span>
                </div>
                <div className="flex items-start gap-2 text-sm text-gray-500">
                  <MapPin size={14} className="mt-0.5 shrink-0" />
                  <span>
                    收件人：{data.receiverName} {data.receiverPhone}
                    <br />
                    {data.receiverAddress}
                  </span>
                </div>
              </div>

              {/* Timeline */}
              <div className="relative pl-8">
                {/* Vertical line */}
                <div className="absolute left-[13px] top-2 bottom-2 w-0.5 bg-gray-200" />

                {data.traceList.map((trace, index) => {
                  const isFirst = index === 0
                  const isLast = index === data.traceList.length - 1
                  const isSigned = trace.statusCode === 10

                  return (
                    <div key={index} className="relative pb-6 last:pb-0">
                      {/* Timeline dot */}
                      <div className="absolute -left-8 top-1">
                        {isLast && isSigned ? (
                          <CheckCircle2 size={26} className="text-green-500 fill-green-500" />
                        ) : isLast ? (
                          <div className="w-[14px] h-[14px] bg-[#e02020] border-2 border-white rounded-full shadow" style={{ boxShadow: "0 0 0 2px #e02020" }} />
                        ) : (
                          <Circle size={14} className="text-gray-300 fill-white" />
                        )}
                      </div>

                      {/* Content */}
                      <div>
                        <p
                          className={`text-sm font-medium ${
                            isLast ? (isSigned ? "text-green-600" : "text-[#e02020]") : "text-gray-500"
                          }`}
                        >
                          {trace.statusText}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          {trace.location && (
                            <span className="text-xs text-gray-400">{trace.location}</span>
                          )}
                          {trace.traceTime && (
                            <span className="text-xs text-gray-400">
                              {trace.traceTime?.replace("T", " ")}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}

                {/* No traces state */}
                {data.traceList.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    <Package size={36} className="mx-auto mb-2 text-gray-300" />
                    <p>暂无物流信息</p>
                    <p className="text-xs mt-1">物流信息将在发货后更新</p>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}
