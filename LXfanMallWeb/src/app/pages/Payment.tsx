import { useNavigate, useSearchParams } from "react-router"
import { orderApi } from "@/utils/api"
import { useEffect, useState } from "react"
import { Loader2, ChevronRight, Check } from "lucide-react"
import { toast } from "sonner"

export function Payment() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const idsParam = searchParams.get("ids") || ""
  const orderIds = idsParam.split(",").filter(Boolean).map(Number)
  const initialPayType = parseInt(searchParams.get("payType") || "0")

  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [payType, setPayType] = useState(initialPayType || 1)
  const [step, setStep] = useState<"select" | "paying" | "done">(initialPayType ? "paying" : "select")

  useEffect(() => {
    if (orderIds.length === 0) {
      setLoading(false)
      return
    }
    Promise.all(
      orderIds.map((id) =>
        orderApi.getDetail(id).catch(() => null)
      )
    ).then((results) => {
      setOrders(results.filter(Boolean))
    }).finally(() => setLoading(false))
  }, [idsParam])

  const totalAmount = orders.reduce((sum, o) => {
    return sum + parseFloat(String(o.payAmount || o.totalAmount || 0))
  }, 0)

  const handleStartPay = () => {
    setStep("paying")
  }

  const handleConfirmPay = async () => {
    try {
      await Promise.all(
        orders.map((o) => orderApi.paySuccess(o.id, payType) as any)
      )
      setStep("done")
      toast.success("支付成功")
    } catch (err: any) {
      const detail = err?.response?.data?.message || err?.message || "支付失败"
      toast.error(`支付失败: ${detail}`)
    }
  }

  const handleCancel = () => {
    navigate("/orders")
  }

  if (loading) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 flex justify-center">
        <Loader2 className="animate-spin text-[#e02020]" size={48} />
      </div>
    )
  }

  if (orders.length === 0) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 text-center">
        <p className="text-gray-500 text-lg mb-4">订单不存在</p>
        <button onClick={() => navigate("/orders")}
          className="text-[#e02020] hover:underline">返回订单列表</button>
      </div>
    )
  }

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1 text-sm text-gray-500 mb-6">
        <button onClick={() => navigate("/orders")} className="hover:text-[#e02020] cursor-pointer">我的订单</button>
        <ChevronRight size={14} />
        <span className="text-gray-800">订单支付</span>
      </div>

      {/* Order Info Card */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
        <div className="flex items-center gap-4">
          {orders.length === 1 && orders[0].orderItemList && orders[0].orderItemList.length > 0 && (
            <div className="flex -space-x-2">
              {orders[0].orderItemList.slice(0, 3).map((item: any, idx: number) => (
                <img key={idx}
                  src={item.productPic || ""}
                  alt={item.productName}
                  className="w-14 h-14 rounded-lg border-2 border-white object-cover bg-gray-100"
                />
              ))}
            </div>
          )}
          <div className="flex-1">
            <p className="text-sm text-gray-500">
              {orders.length > 1
                ? `共 ${orders.length} 个订单`
                : `订单号: ${orders[0]?.orderSn || orders[0]?.id}`}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              {orders.length === 1 ? orders[0]?.createTime?.slice(0, 10) : `合计金额`}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">应付金额</p>
            <p className="text-2xl font-bold text-[#e02020]">¥{totalAmount.toFixed(2)}</p>
          </div>
        </div>

        {/* Multiple order list */}
        {orders.length > 1 && (
          <div className="mt-4 pt-4 border-t border-gray-100 space-y-2">
            {orders.map((o, idx) => (
              <div key={o.id} className="flex items-center justify-between text-sm">
                <span className="text-gray-500">订单 {idx + 1}: <span className="font-mono text-gray-700">{o.orderSn}</span></span>
                <span className="text-gray-700 font-medium">¥{parseFloat(String(o.payAmount || o.totalAmount || 0)).toFixed(2)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Step: Select Payment Method */}
      {step === "select" && (
        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">选择支付方式</h2>
          <div className="space-y-3">
            <label
              onClick={() => setPayType(1)}
              className={`flex items-center gap-4 p-4 border-2 rounded-xl cursor-pointer transition-all ${payType === 1 ? "border-[#e02020] bg-red-50" : "border-gray-100 hover:border-gray-300"}`}
            >
              <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${payType === 1 ? "border-[#e02020] bg-[#e02020]" : "border-gray-300"}`}>
                {payType === 1 && <Check size={14} className="text-white" />}
              </div>
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V6h16v12z"/>
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800">支付宝支付</p>
                <p className="text-xs text-gray-400">推荐支付宝用户使用</p>
              </div>
            </label>

            <label
              onClick={() => setPayType(2)}
              className={`flex items-center gap-4 p-4 border-2 rounded-xl cursor-pointer transition-all ${payType === 2 ? "border-[#e02020] bg-red-50" : "border-gray-100 hover:border-gray-300"}`}
            >
              <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${payType === 2 ? "border-[#e02020] bg-[#e02020]" : "border-gray-300"}`}>
                {payType === 2 && <Check size={14} className="text-white" />}
              </div>
              <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800">微信支付</p>
                <p className="text-xs text-gray-400">推荐微信用户使用</p>
              </div>
            </label>
          </div>

          <div className="flex gap-3 mt-6">
            <button onClick={handleCancel}
              className="flex-1 py-3 border border-gray-200 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors">
              取消支付
            </button>
            <button onClick={handleStartPay}
              className="flex-1 bg-[#e02020] text-white py-3 rounded-lg font-medium hover:bg-[#c01010] transition-colors">
              立即支付 ¥{totalAmount.toFixed(2)}
            </button>
          </div>
        </div>
      )}

      {/* Step: Payment Interface (QR Code Placeholder) */}
      {step === "paying" && (
        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4 text-center">
            {payType === 1 ? "支付宝支付" : "微信支付"}
          </h2>
          <div className="flex flex-col items-center py-6">
            {/* QR Code Placeholder */}
            <div className="w-48 h-48 bg-gray-100 rounded-xl flex items-center justify-center border-2 border-dashed border-gray-300 mb-4">
              <div className="text-center">
                <svg className="w-12 h-12 mx-auto text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"/>
                </svg>
                <p className="text-sm text-gray-400">二维码区域</p>
                <p className="text-xs text-gray-300 mt-1">请使用{payType === 1 ? "支付宝" : "微信"}扫码支付</p>
              </div>
            </div>

            <div className="text-center mb-6">
              <p className="text-sm text-gray-500">应付金额</p>
              <p className="text-3xl font-bold text-[#e02020]">¥{totalAmount.toFixed(2)}</p>
            </div>

            <div className="flex gap-3 w-full max-w-xs">
              <button onClick={handleCancel}
                className="flex-1 py-3 border border-gray-200 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                取消支付
              </button>
              <button onClick={handleConfirmPay}
                className="flex-1 bg-[#e02020] text-white py-3 rounded-lg font-medium hover:bg-[#c01010] transition-colors">
                我已支付
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-3">支付成功后请点击"我已支付"按钮</p>
          </div>
        </div>
      )}

      {/* Step: Payment Done */}
      {step === "done" && (
        <div className="bg-white rounded-xl p-16 shadow-sm text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">支付成功</h2>
          <p className="text-gray-500 mb-2">¥{totalAmount.toFixed(2)}</p>
          <p className="text-sm text-gray-400 mb-8">订单已进入待发货状态</p>
          <div className="flex gap-4 justify-center">
            <button onClick={() => navigate("/orders")}
              className="px-8 py-3 bg-[#e02020] text-white rounded-lg font-medium hover:bg-[#c01010] transition-colors">
              查看订单
            </button>
            <button onClick={() => navigate("/")}
              className="px-8 py-3 border border-gray-200 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors">
              返回首页
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
