import { useNavigate } from "react-router"
import { returnApi } from "@/utils/api"
import { useUserStore } from "@/store/userStore"
import { useAuthModalStore } from "@/store/authModalStore"
import { useEffect, useState } from "react"
import { Package, Loader2, Clock, CheckCircle, XCircle, RefreshCw, ArrowLeft } from "lucide-react"
import { toast } from "sonner"

interface ReturnRecordItem {
  id: number
  orderId: number
  orderSn: string
  productPic: string
  productName: string
  productBrand: string
  productAttr: string
  productCount: number
  productRealPrice: number
  productPrice: number
  reason: string
  description: string
  status: number
  createTime: string
  handleTime: string
  handleNote: string
  returnAmount: number
  receiveTime: string
  receiveNote: string
}

const STATUS_MAP: Record<number, { label: string; color: string; icon: typeof Clock }> = {
  0: { label: "待处理", color: "bg-orange-100 text-orange-600", icon: Clock },
  1: { label: "退货中", color: "bg-blue-100 text-blue-600", icon: RefreshCw },
  2: { label: "已完成", color: "bg-green-100 text-green-600", icon: CheckCircle },
  3: { label: "已拒绝", color: "bg-red-100 text-red-600", icon: XCircle },
}

export function ReturnRecord() {
  const navigate = useNavigate()
  const isAuthenticated = useUserStore((s) => s.isAuthenticated)
  const member = useUserStore((s) => s.member)
  const openAuth = useAuthModalStore((s) => s.openAuth)

  const [list, setList] = useState<ReturnRecordItem[]>([])
  const [loading, setLoading] = useState(true)

  const fetchList = () => {
    if (!member?.username) return
    setLoading(true)
    returnApi.getList(member.username)
      .then((data: any) => {
        setList(Array.isArray(data) ? data : [])
      })
      .catch(() => {
        setList([])
        toast.error("获取售后记录失败")
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (isAuthenticated && member?.username) {
      fetchList()
    } else {
      setLoading(false)
    }
  }, [isAuthenticated, member?.username])

  if (!isAuthenticated) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 text-center">
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Package size={36} className="text-gray-300" />
        </div>
        <p className="text-gray-500 text-lg mb-6">请先登录后查看售后记录</p>
        <button onClick={() => openAuth("login")}
          className="inline-block bg-[#e02020] text-white px-8 py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium">
          立即登录
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8 min-h-[60vh]">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate("/orders")} className="text-gray-400 hover:text-gray-600 transition-colors">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-2xl font-bold text-gray-900">我的售后</h1>
        <span className="text-sm text-gray-400">共 {list.length} 条记录</span>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="animate-spin text-[#e02020]" size={40} />
        </div>
      ) : list.length === 0 ? (
        <div className="bg-white rounded-xl p-16 text-center shadow-sm">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Package size={36} className="text-gray-300" />
          </div>
          <p className="text-gray-500 text-lg mb-2">暂无售后记录</p>
          <p className="text-gray-400 text-sm mb-6">您还没有提交过退货退款申请</p>
          <button onClick={() => navigate("/orders")}
            className="inline-block bg-[#e02020] text-white px-8 py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium">
            查看订单
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {list.map((item) => {
            const s = STATUS_MAP[item.status] || STATUS_MAP[0]
            const Icon = s.icon
            return (
              <div key={item.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-3 bg-gray-50 border-b border-gray-100">
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>售后单号: {item.id}</span>
                    <span className="flex items-center gap-1">
                      <Icon size={14} />
                      <span className={s.color + " px-1.5 py-0.5 rounded-full text-xs font-medium"}>{s.label}</span>
                    </span>
                  </div>
                  <span className="text-xs text-gray-400">{item.createTime?.replace("T", " ") || ""}</span>
                </div>

                {/* Product info */}
                <div className="px-6 py-4 border-b border-gray-50">
                  <div className="flex items-center gap-4">
                    <img src={item.productPic || ""} alt={item.productName}
                      className="w-16 h-16 rounded-lg object-cover bg-gray-100 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{item.productName}</p>
                      {item.productAttr && (
                        <p className="text-xs text-gray-400 mt-0.5">{item.productAttr}</p>
                      )}
                      <p className="text-xs text-gray-400 mt-1">
                        数量: x{item.productCount} &nbsp;|&nbsp; 单价: ¥{parseFloat(String(item.productRealPrice || item.productPrice)).toFixed(2)}
                      </p>
                    </div>
                  </div>
                  {item.reason && (
                    <div className="mt-2 text-xs text-gray-500">
                      <span className="text-gray-400">退货原因:</span> {item.reason}
                    </div>
                  )}
                  {item.description && (
                    <div className="mt-1 text-xs text-gray-500">
                      <span className="text-gray-400">问题描述:</span> {item.description}
                    </div>
                  )}
                </div>

                {/* Status details */}
                <div className="px-6 py-3 flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-4 text-xs text-gray-400">
                    {item.status === 1 && item.handleTime && (
                      <span>处理时间: {item.handleTime?.replace("T", " ")}</span>
                    )}
                    {(item.status === 2 || item.status === 3) && item.handleTime && (
                      <span>处理时间: {item.handleTime?.replace("T", " ")}</span>
                    )}
                    {item.status === 2 && item.returnAmount && (
                      <span className="text-[#e02020] font-medium">退款金额: ¥{parseFloat(String(item.returnAmount)).toFixed(2)}</span>
                    )}
                    {item.status === 3 && item.handleNote && (
                      <span>拒绝原因: {item.handleNote}</span>
                    )}
                    {item.status === 2 && item.receiveNote && (
                      <span>收货备注: {item.receiveNote}</span>
                    )}
                  </div>
                  <button onClick={() => navigate(`/orders?orderId=${item.orderId}`)}
                    className="text-xs text-[#e02020] hover:underline flex-shrink-0">
                    查看订单
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
