import { Link, useNavigate } from "react-router"
import { orderApi } from "@/utils/api"
import { useUserStore } from "@/store/userStore"
import { useAuthModalStore } from "@/store/authModalStore"
import { useEffect, useState } from "react"
import { Package, Loader2, Truck, MessageSquare } from "lucide-react"
import { toast } from "sonner"
import { OrderLogisticsModal } from "@/app/components/OrderLogisticsModal"
import { ReviewModal } from "@/app/components/ReviewModal"
import { OrderCountdown } from "@/app/components/OrderCountdown"

function getStatusInfo(status: number) {
  const map: Record<number, { label: string; color: string }> = {
    0: { label: "待付款", color: "bg-orange-100 text-orange-600" },
    1: { label: "待发货", color: "bg-blue-100 text-blue-600" },
    2: { label: "已发货", color: "bg-purple-100 text-purple-600" },
    7: { label: "已送达", color: "bg-cyan-100 text-cyan-600" },
    3: { label: "已完成", color: "bg-green-100 text-green-600" },
    4: { label: "已关闭", color: "bg-gray-100 text-gray-500" },
    5: { label: "已退货", color: "bg-red-100 text-red-600" },
    6: { label: "已评价", color: "bg-teal-100 text-teal-600" },
  }
  return map[status] || { label: "未知", color: "bg-gray-100 text-gray-500" }
}

interface OrderItem {
  id: number
  orderSn: string
  createTime: string
  totalAmount: number
  payAmount: number
  status: number
  commentTime?: string
  orderItemList?: any[]
}

export function Orders() {
  const navigate = useNavigate()
  const isAuthenticated = useUserStore((s) => s.isAuthenticated)
  const openAuth = useAuthModalStore((s) => s.openAuth)
  const [orders, setOrders] = useState<OrderItem[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState(-1)
  const [pageNum, setPageNum] = useState(1)
  const [total, setTotal] = useState(0)
  const [trackingOrderId, setTrackingOrderId] = useState<number | null>(null)
  const [logisticsOpen, setLogisticsOpen] = useState(false)

  // 评价弹窗状态
  const [reviewOrderId, setReviewOrderId] = useState<number>(0)
  const [reviewItems, setReviewItems] = useState<any[]>([])
  const [reviewOpen, setReviewOpen] = useState(false)

  const fetchOrders = () => {
    setLoading(true)
    orderApi.getList({ status: activeTab, pageNum, pageSize: 10 })
      .then((data: any) => {
        setOrders(data?.list || data?.records || [])
        setTotal(data?.total || data?.totalElements || 0)
      })
      .catch(() => setOrders([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchOrders() }, [activeTab, pageNum])

  const handleCancel = (orderId: number) => {
    if (!confirm("确定要取消该订单吗？")) return
    orderApi.cancelOrder(orderId).then(() => {
      toast.success("订单已取消")
      setOrders((prev) => prev.map((o) => o.id === orderId ? { ...o, status: 4 } : o))
    }).catch(() => toast.error("取消失败"))
  }

  const handleOrderExpired = (orderId: number) => {
    setOrders((prev) => prev.map((o) => o.id === orderId ? { ...o, status: 4 } : o))
  }

  const handleConfirmReceive = (orderId: number) => {
    if (!confirm("确认已收到货物？")) return
    orderApi.confirmReceive(orderId).then(() => {
      toast.success("已确认收货")
      setOrders((prev) => prev.map((o) => o.id === orderId ? { ...o, status: 3 } : o))
    }).catch(() => toast.error("操作失败"))
  }

  const handleDelete = (orderId: number) => {
    if (!confirm("确定要删除该订单吗？")) return
    orderApi.deleteOrder(orderId).then(() => {
      toast.success("订单已删除")
      setOrders((prev) => prev.filter((o) => o.id !== orderId))
    }).catch(() => toast.error("删除失败"))
  }

  const handleOpenReview = (order: any) => {
    const formatAttr = (raw: string) => {
      if (!raw) return ""
      try {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed)) {
          return parsed.map((a: any) => `${a.key}:${a.value}`).join(" ")
        }
      } catch { /* ignore */ }
      return raw
    }
    const items = (order.orderItemList || []).map((item: any) => ({
      orderItemId: item.id,
      productId: item.productId,
      productName: item.productName || "",
      productPic: item.productPic || "",
      productPrice: item.productPrice || "0",
      productQuantity: item.productQuantity || 1,
      productAttribute: formatAttr(item.productAttr || ""),
    }))
    setReviewOrderId(order.id)
    setReviewItems(items)
    setReviewOpen(true)
  }

  const handleReviewSuccess = () => {
    fetchOrders()
  }

  const tabs = [
    { value: -1, label: "全部" },
    { value: 0, label: "待付款" },
    { value: 1, label: "待发货" },
    { value: 2, label: "已发货" },
    { value: 7, label: "已送达" },
    { value: 3, label: "已完成" },
    { value: 4, label: "已关闭" },
    { value: 5, label: "已退货" },
    { value: 6, label: "已评价" },
  ]

  if (!isAuthenticated) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 text-center">
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Package size={36} className="text-gray-300" />
        </div>
        <p className="text-gray-500 text-lg mb-6">请先登录后查看订单</p>
        <button onClick={() => openAuth("login")}
          className="inline-block bg-[#e02020] text-white px-8 py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium">
          立即登录
        </button>
      </div>
    )
  }

  return (
    <>
    <div className="max-w-[1440px] mx-auto px-6 py-8 min-h-[60vh]">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-900">我的订单</h1>
        <button onClick={() => navigate("/return-record")}
          className="text-sm text-[#e02020] hover:text-[#c01010] transition-colors font-medium flex items-center gap-1">
          我的售后 &rarr;
        </button>
      </div>
      <p className="text-sm text-gray-500 mb-6">共 {total} 个订单</p>

      {/* Status Tabs */}
      <div className="bg-white rounded-xl p-2 shadow-sm mb-6 flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button key={tab.value} onClick={() => { setActiveTab(tab.value); setPageNum(1) }}
            className={`px-5 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${activeTab === tab.value ? "bg-[#e02020] text-white" : "text-gray-600 hover:bg-gray-100"}`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Order List */}
      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#e02020]" size={40} /></div>
      ) : orders.length === 0 ? (
        <div className="bg-white rounded-xl p-16 text-center shadow-sm">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Package size={36} className="text-gray-300" />
          </div>
          <p className="text-gray-500 text-lg mb-4">暂无订单</p>
          <Link to="/" className="inline-block bg-[#e02020] text-white px-8 py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium">
            去逛逛
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => {
            // 已退货tab下强制覆盖显示状态为5
            const isReturnTab = activeTab === 5
            const isReviewTab = activeTab === 6
            const displayStatus = isReturnTab ? 5 : (isReviewTab ? 6 : order.status)
            const s = getStatusInfo(displayStatus)
            return (
              <div key={order.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-3 bg-gray-50 border-b border-gray-100">
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>订单号: <span className="text-gray-700">{order.orderSn || order.id}</span></span>
                    <span>{order.createTime?.slice(0, 10)}</span>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${s.color}`}>{s.label}</span>
                </div>

                {/* Items preview */}
                {order.orderItemList && order.orderItemList.length > 0 && (
                  <div className="px-6 py-3 border-b border-gray-50">
                    {order.orderItemList.slice(0, 3).map((item: any, idx: number) => (
                      <div key={idx} className="flex items-center gap-3 py-1.5">
                        <img src={item.productPic || ""} alt={item.productName}
                          className="w-12 h-12 rounded-lg object-cover bg-gray-100" />
                        <span className="text-sm text-gray-700 line-clamp-1 flex-1">{item.productName}</span>
                        <span className="text-sm text-gray-500">x{item.productQuantity}</span>
                        <span className="text-sm text-gray-700 w-16 text-right">¥{parseFloat(item.productPrice || 0).toFixed(2)}</span>
                      </div>
                    ))}
                    {order.orderItemList.length > 3 && (
                      <p className="text-xs text-gray-400 mt-1">...共 {order.orderItemList.length} 件商品</p>
                    )}
                  </div>
                )}

                {/* Footer */}
                <div className="flex items-center justify-between px-6 py-3">
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-600">
                      {displayStatus === 0 ? "应付" : "已付"}: <span className="text-[#e02020] font-bold text-base">¥{parseFloat(String(order.payAmount || order.totalAmount || 0)).toFixed(2)}</span>
                    </span>
                    {displayStatus === 0 && order.createTime && (
                      <OrderCountdown
                        createTime={order.createTime}
                        timeoutMinutes={15}
                        onExpired={() => handleOrderExpired(order.id)}
                      />
                    )}
                  </div>
                  <div className="flex gap-2">
                    {displayStatus === 0 && (
                      <>
                        <button onClick={() => handleCancel(order.id)}
                          className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                          取消订单
                        </button>
                        <button onClick={() => navigate(`/payment?ids=${order.id}`)}
                          className="px-4 py-1.5 text-sm bg-[#e02020] text-white rounded-lg hover:bg-[#c01010] transition-colors">
                          立即付款
                        </button>
                      </>
                    )}
                    {(displayStatus === 2 || displayStatus === 7) && (
                      <>
                        <button onClick={() => navigate(`/return-apply?orderId=${order.id}`)}
                          className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-red-50 hover:text-red-500 hover:border-red-300 transition-colors">
                          申请退货
                        </button>
                        <button onClick={() => { setTrackingOrderId(order.id); setLogisticsOpen(true) }}
                          className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1">
                          <Truck size={14} />
                          查看物流
                        </button>
                        <button onClick={() => handleConfirmReceive(order.id)}
                          className="px-4 py-1.5 text-sm bg-[#e02020] text-white rounded-lg hover:bg-[#c01010] transition-colors">
                          确认收货
                        </button>
                      </>
                    )}
                    {displayStatus === 3 && (
                      <>
                        {order.commentTime ? (
                          <>
                            <button onClick={() => navigate(`/product/${order.orderItemList?.[0]?.productId || ''}`)}
                              className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1">
                              <MessageSquare size={14} /> 查看评价
                            </button>
                            <button onClick={() => handleDelete(order.id)}
                              className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-red-50 hover:text-red-500 hover:border-red-300 transition-colors">
                              删除订单
                            </button>
                          </>
                        ) : (
                          <>
                            <button onClick={() => handleOpenReview(order)}
                              className="px-4 py-1.5 text-sm bg-[#e02020] text-white rounded-lg hover:bg-[#c01010] transition-colors flex items-center gap-1">
                              <MessageSquare size={14} /> 评价
                            </button>
                            {Date.now() - new Date(order.createTime).getTime() < 7 * 24 * 60 * 60 * 1000 && (
                              <button onClick={() => navigate(`/return-apply?orderId=${order.id}`)}
                                className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-red-50 hover:text-red-500 hover:border-red-300 transition-colors">
                                申请退货
                              </button>
                            )}
                            <button onClick={() => handleDelete(order.id)}
                              className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-red-50 hover:text-red-500 hover:border-red-300 transition-colors">
                              删除订单
                            </button>
                          </>
                        )}
                      </>
                    )}
                    {displayStatus === 5 && (
                      <button onClick={() => navigate("/return-record")}
                        className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        查看售后
                      </button>
                    )}
                    {displayStatus === 6 && (
                      <>
                        {order.orderItemList?.[0]?.productId && (
                          <button onClick={() => navigate(`/product/${order.orderItemList[0].productId}`)}
                            className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1">
                            <MessageSquare size={14} /> 查看评价
                          </button>
                        )}
                        <button onClick={() => handleDelete(order.id)}
                          className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-red-50 hover:text-red-500 hover:border-red-300 transition-colors">
                          删除订单
                        </button>
                      </>
                    )}
                    {displayStatus === 4 && (
                      <button onClick={() => handleDelete(order.id)}
                        className="px-4 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-red-50 hover:text-red-500 hover:border-red-300 transition-colors">
                        删除订单
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>

      {/* Logistics Modal */}
      {trackingOrderId && (
        <OrderLogisticsModal
          orderId={trackingOrderId}
          open={logisticsOpen}
          onClose={() => setLogisticsOpen(false)}
        />
      )}

      {/* Review Modal */}
      <ReviewModal
        orderId={reviewOrderId}
        items={reviewItems}
        open={reviewOpen}
        onClose={() => setReviewOpen(false)}
        onSuccess={handleReviewSuccess}
      />
    </>
  )
}
