import { useNavigate, useSearchParams } from "react-router"
import { orderApi, returnApi } from "@/utils/api"
import { useUserStore } from "@/store/userStore"
import { useEffect, useState } from "react"
import { ArrowLeft, Loader2, Upload } from "lucide-react"
import { toast } from "sonner"

const RETURN_REASONS = [
  "商品质量问题",
  "商品与描述不符",
  "商品破损/配件缺失",
  "尺码不合适",
  "颜色/款式不想要了",
  "收到商品与订单不符",
  "七天无理由退货",
  "其他",
]

interface OrderItem {
  id: number
  productId: number
  productPic: string
  productName: string
  productBrand: string
  productAttr: string
  productQuantity: number
  productPrice: number
  productRealPrice?: number
}

interface OrderDetail {
  id: number
  orderSn: string
  createTime: string
  status: number
  orderItemList: OrderItem[]
  memberUsername?: string
}

export function ReturnApply() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const orderId = searchParams.get("orderId")
  const member = useUserStore((s) => s.member)

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [order, setOrder] = useState<OrderDetail | null>(null)

  // Form state
  const [selectedItem, setSelectedItem] = useState<OrderItem | null>(null)
  const [reason, setReason] = useState("")
  const [description, setDescription] = useState("")
  const [returnName, setReturnName] = useState(member?.nickname || member?.username || "")
  const [returnPhone, setReturnPhone] = useState(member?.phone || "")
  const [proofPics, setProofPics] = useState("")

  useEffect(() => {
    if (!orderId) return
    setLoading(true)
    orderApi.getDetail(Number(orderId))
      .then((data: any) => {
        const detail = data?.data || data
        setOrder(detail)
        // Pre-select the first item
        if (detail?.orderItemList?.length > 0) {
          setSelectedItem(detail.orderItemList[0])
        }
      })
      .catch(() => toast.error("获取订单信息失败"))
      .finally(() => setLoading(false))
  }, [orderId])

  // Ensure member info is filled in
  useEffect(() => {
    if (member) {
      setReturnName((prev) => prev || member.nickname || member.username || "")
      setReturnPhone((prev) => prev || member.phone || "")
    }
  }, [member])

  const canSubmit = selectedItem && reason && returnName && returnPhone

  const handleSubmit = async () => {
    if (!canSubmit || !order || !selectedItem || !member) return
    setSubmitting(true)
    try {
      await returnApi.create({
        orderId: order.id,
        productId: selectedItem.productId,
        orderSn: order.orderSn,
        memberUsername: member.nickname || member.username,
        returnName,
        returnPhone,
        productPic: selectedItem.productPic,
        productName: selectedItem.productName,
        productBrand: selectedItem.productBrand || "",
        productAttr: selectedItem.productAttr || "",
        productCount: selectedItem.productQuantity,
        productPrice: selectedItem.productPrice,
        productRealPrice: selectedItem.productRealPrice || selectedItem.productPrice,
        reason,
        description,
        proofPics,
      })
      toast.success("退货申请已提交，请等待审核")
      navigate("/orders")
    } catch {
      toast.error("提交失败，请稍后重试")
    } finally {
      setSubmitting(false)
    }
  }

  if (!orderId) {
    return (
      <div className="max-w-[800px] mx-auto px-6 py-20 text-center">
        <p className="text-gray-500">参数错误，请返回订单列表重试</p>
        <button onClick={() => navigate("/orders")} className="mt-4 text-[#e02020] hover:underline">返回订单列表</button>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="animate-spin text-[#e02020]" size={40} />
      </div>
    )
  }

  if (!order) {
    return (
      <div className="max-w-[800px] mx-auto px-6 py-20 text-center">
        <p className="text-gray-500">订单不存在</p>
        <button onClick={() => navigate("/orders")} className="mt-4 text-[#e02020] hover:underline">返回订单列表</button>
      </div>
    )
  }

  return (
    <div className="max-w-[800px] mx-auto px-6 py-8 min-h-[60vh]">
      {/* Header */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-4 transition-colors">
        <ArrowLeft size={18} />
        <span className="text-sm">返回</span>
      </button>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">申请退货</h1>
      <p className="text-sm text-gray-500 mb-6">订单号: {order.orderSn || order.id}</p>

      {/* Order items - select which to return */}
      <section className="bg-white rounded-xl shadow-sm p-6 mb-4">
        <h2 className="text-base font-semibold text-gray-900 mb-3">选择退货商品</h2>
        {order.orderItemList?.length > 1 && (
          <p className="text-xs text-gray-400 mb-3">该订单有多个商品，请选择要退货的商品</p>
        )}
        <div className="space-y-3">
          {order.orderItemList?.map((item) => (
            <label
              key={item.id}
              className={`flex items-center gap-4 p-3 rounded-lg border-2 cursor-pointer transition-colors ${
                selectedItem?.id === item.id
                  ? "border-[#e02020] bg-red-50"
                  : "border-gray-100 hover:border-gray-200"
              }`}
            >
              <input
                type="radio"
                name="returnItem"
                checked={selectedItem?.id === item.id}
                onChange={() => setSelectedItem(item)}
                className="accent-[#e02020]"
              />
              <img
                src={item.productPic || ""}
                alt={item.productName}
                className="w-16 h-16 rounded-lg object-cover bg-gray-100 flex-shrink-0"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{item.productName}</p>
                {item.productAttr && (
                  <p className="text-xs text-gray-400 mt-0.5">{item.productAttr}</p>
                )}
                {item.productBrand && (
                  <p className="text-xs text-gray-400">{item.productBrand}</p>
                )}
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-sm text-gray-900">¥{parseFloat(String(item.productRealPrice || item.productPrice)).toFixed(2)}</p>
                <p className="text-xs text-gray-400">x{item.productQuantity}</p>
              </div>
            </label>
          ))}
        </div>
      </section>

      {/* Return reason */}
      <section className="bg-white rounded-xl shadow-sm p-6 mb-4">
        <h2 className="text-base font-semibold text-gray-900 mb-3">
          退货原因 <span className="text-[#e02020]">*</span>
        </h2>
        <select
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#e02020] bg-white"
        >
          <option value="">请选择退货原因</option>
          {RETURN_REASONS.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </section>

      {/* Description */}
      <section className="bg-white rounded-xl shadow-sm p-6 mb-4">
        <h2 className="text-base font-semibold text-gray-900 mb-3">问题描述</h2>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="请详细描述您遇到的问题，如商品损坏情况、缺失配件等..."
          rows={4}
          className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#e02020] resize-none"
        />
      </section>

      {/* Proof images */}
      <section className="bg-white rounded-xl shadow-sm p-6 mb-4">
        <h2 className="text-base font-semibold text-gray-900 mb-3">凭证图片（选填）</h2>
        <p className="text-xs text-gray-400 mb-2">可上传商品照片、破损细节等凭证，多个图片链接请用逗号分隔</p>
        <div className="flex items-center gap-3">
          <input
            value={proofPics}
            onChange={(e) => setProofPics(e.target.value)}
            placeholder="输入图片URL，多张请用逗号分隔"
            className="flex-1 px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#e02020]"
          />
          <div className="p-2.5 bg-gray-50 rounded-lg text-gray-400">
            <Upload size={18} />
          </div>
        </div>
      </section>

      {/* Contact info */}
      <section className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h2 className="text-base font-semibold text-gray-900 mb-3">联系信息</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">联系人 <span className="text-[#e02020]">*</span></label>
            <input
              value={returnName}
              onChange={(e) => setReturnName(e.target.value)}
              placeholder="退货联系人姓名"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#e02020]"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">联系电话 <span className="text-[#e02020]">*</span></label>
            <input
              value={returnPhone}
              onChange={(e) => setReturnPhone(e.target.value)}
              placeholder="退货联系电话"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#e02020]"
            />
          </div>
        </div>
      </section>

      {/* Submit */}
      <div className="flex items-center justify-end gap-3 mb-8">
        <button
          onClick={() => navigate("/orders")}
          className="px-6 py-2.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          取消
        </button>
        <button
          onClick={handleSubmit}
          disabled={!canSubmit || submitting}
          className={`px-8 py-2.5 text-sm text-white rounded-lg font-medium transition-colors flex items-center gap-2 ${
            canSubmit && !submitting
              ? "bg-[#e02020] hover:bg-[#c01010]"
              : "bg-gray-300 cursor-not-allowed"
          }`}
        >
          {submitting && <Loader2 className="animate-spin" size={16} />}
          {submitting ? "提交中..." : "提交申请"}
        </button>
      </div>
    </div>
  )
}
