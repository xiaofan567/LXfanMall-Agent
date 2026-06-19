import { Link, useNavigate } from "react-router"
import { orderApi, cartApi, addressApi } from "@/utils/api"
import { useUserStore } from "@/store/userStore"
import { useAuthModalStore } from "@/store/authModalStore"
import { useEffect, useState } from "react"
import { MapPin, Plus, Loader2, Package, X } from "lucide-react"
import { toast } from "sonner"

interface Address {
  id: number
  name: string
  phoneNumber: string
  province: string
  city: string
  region: string
  detailAddress: string
  defaultStatus: number
}

interface ConfirmOrderItem {
  id: number
  productId: number
  productName: string
  productPic: string
  price: number
  quantity: number
  productSubTitle?: string
}

interface ConfirmOrder {
  cartPromotionItemList?: ConfirmOrderItem[]
  memberReceiveAddressList?: Address[]
  couponHistoryDetailList?: any[]
  calcAmount?: {
    totalAmount: number
    freightAmount: number
    promotionAmount: number
    payAmount: number
    integrationAmount?: number
    couponAmount?: number
  }
}

export function Order() {
  const navigate = useNavigate()
  const isAuthenticated = useUserStore((s) => s.isAuthenticated)
  const openAuth = useAuthModalStore((s) => s.openAuth)
  const [order, setOrder] = useState<ConfirmOrder | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [selectedAddressId, setSelectedAddressId] = useState<number>(0)
  const [note, setNote] = useState("")
  const [showAddressModal, setShowAddressModal] = useState(false)
  const [addressForm, setAddressForm] = useState({
    name: "",
    phoneNumber: "",
    province: "",
    city: "",
    region: "",
    detailAddress: "",
    postCode: "",
    defaultStatus: 0 as 0 | 1,
  })
  const [savingAddress, setSavingAddress] = useState(false)
  const [payType, setPayType] = useState(1) // 1-支付宝 2-微信

  const reloadOrder = async () => {
    try {
      const cartList: any = await cartApi.getList()
      const items = Array.isArray(cartList) ? cartList : (cartList?.list || cartList?.records || [])
      if (items.length === 0) return
      const cartIds = items.map((i: any) => i.id)
      const confirmOrder: any = await orderApi.generateConfirmOrder(cartIds)
      setOrder(confirmOrder)
      const addrList = confirmOrder?.memberReceiveAddressList || confirmOrder?.addressList || []
      if (addrList.length > 0) {
        const defaultAddr = addrList.find((a: Address) => a.defaultStatus === 1) || addrList[0]
        setSelectedAddressId(defaultAddr.id)
      }
    } catch (err: any) {
      const detail = err?.response?.data?.message || err?.message || String(err)
      console.error("[Order] 刷新订单信息失败:", detail)
    }
  }

  const resetAddressForm = () => {
    setAddressForm({ name: "", phoneNumber: "", province: "", city: "", region: "", detailAddress: "", postCode: "", defaultStatus: 0 })
  }

  const handleAddAddress = async () => {
    const { name, phoneNumber, province, city, region, detailAddress } = addressForm
    if (!name.trim()) { toast.error("请输入收货人姓名"); return }
    if (!phoneNumber.trim()) { toast.error("请输入手机号码"); return }
    if (!province.trim()) { toast.error("请输入省份"); return }
    if (!city.trim()) { toast.error("请输入城市"); return }
    if (!region.trim()) { toast.error("请输入区/县"); return }
    if (!detailAddress.trim()) { toast.error("请输入详细地址"); return }

    setSavingAddress(true)
    try {
      await addressApi.add(addressForm)
      setSavingAddress(false)
      toast.success("地址添加成功")
      setShowAddressModal(false)
      resetAddressForm()
      await reloadOrder()
    } catch (err: any) {
      const detail = err?.response?.data?.message || err?.message || String(err)
      queueMicrotask(() => {
        setSavingAddress(false)
        toast.error(`添加地址失败: ${detail}`)
      })
    }
  }

  // We load cart items to get their IDs for confirm order
  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false)
      toast.error("请先登录后再下单")
      openAuth("login")
      return
    }
    const fetchData = async () => {
      try {
        const cartList: any = await cartApi.getList()
        const items = Array.isArray(cartList) ? cartList : (cartList?.list || cartList?.records || [])
        if (items.length === 0) {
          setLoading(false)
          return
        }
        const cartIds = items.map((i: any) => i.id)
        const confirmOrder: any = await orderApi.generateConfirmOrder(cartIds)
        setOrder(confirmOrder)
        const addrList = confirmOrder?.memberReceiveAddressList || confirmOrder?.addressList || []
        const defaultAddr = addrList.find((a: Address) => a.defaultStatus === 1) || addrList[0]
        if (defaultAddr) setSelectedAddressId(defaultAddr.id)
      } catch (err: any) {
        const detail = err?.response?.data?.message || err?.message || String(err)
        console.error("[Order] 加载订单信息失败:", detail)
        queueMicrotask(() => toast.error(`加载订单信息失败: ${detail}`))
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleSubmit = async () => {
    if (!selectedAddressId) {
      toast.error("请选择收货地址")
      return
    }
    if (!order?.cartPromotionItemList?.length) {
      toast.error("没有可结算的商品")
      return
    }
    setSubmitting(true)
    try {
      // 逐个商品串行提交订单，避免并发事务冲突
      const cartIds = order.cartPromotionItemList.map((i) => i.id)
      const orders: any[] = []
      for (const cartId of cartIds) {
        const result: any = await orderApi.generateOrder({
          cartIds: [cartId],
          memberReceiveAddressId: selectedAddressId,
          useIntegration: 0,
          payType,
        })
        if (result?.order) orders.push(result.order)
      }
      setSubmitting(false)
      if (orders.length === 0) {
        toast.error("下单失败：未能创建有效订单")
        return
      }
      const ids = orders.map((o) => o.id).join(",")
      navigate(`/payment?ids=${ids}&payType=${payType}`)
    } catch (err: any) {
      const detail = err?.response?.data?.message || err?.message || String(err)
      setSubmitting(false)
      toast.error(`下单失败: ${detail}`)
    }
  }

  if (loading) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 flex justify-center">
        <Loader2 className="animate-spin text-[#e02020]" size={48} />
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 text-center">
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Package size={36} className="text-gray-300" />
        </div>
        <p className="text-gray-500 text-lg mb-6">请先登录后再下单</p>
        <button onClick={() => openAuth("login")}
          className="inline-block bg-[#e02020] text-white px-8 py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium">
          立即登录
        </button>
      </div>
    )
  }

  const cartItems = order?.cartPromotionItemList || []
  const addresses = order?.memberReceiveAddressList || []
  const amount = order?.calcAmount || { totalAmount: 0, freightAmount: 0, payAmount: 0, promotionAmount: 0 }
  const totalAmount = amount.totalAmount || cartItems.reduce((s: number, i: ConfirmOrderItem) => s + i.price * i.quantity, 0)
  const payAmount = amount.payAmount || totalAmount

  if (cartItems.length === 0) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 text-center">
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Package size={36} className="text-gray-300" />
        </div>
        <p className="text-gray-500 text-lg mb-4">购物车为空，请先添加商品</p>
        <Link to="/" className="text-[#e02020] hover:underline">去逛逛</Link>
      </div>
    )
  }

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">确认订单</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Address + Items */}
        <div className="lg:col-span-2 space-y-6">
          {/* Shipping Address */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <MapPin size={20} className="text-[#e02020]" />收货地址
              </h2>
              <button onClick={() => { resetAddressForm(); setShowAddressModal(true) }}
                className="text-sm text-[#e02020] hover:underline flex items-center gap-1">
                <Plus size={14} /> 添加新地址
              </button>
            </div>
            {addresses.length === 0 ? (
              <p className="text-gray-500 text-sm py-4 text-center">暂无收货地址，请先添加</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {addresses.map((addr: Address) => (
                  <button key={addr.id} onClick={() => setSelectedAddressId(addr.id)}
                    className={`text-left p-4 rounded-lg border-2 transition-all ${selectedAddressId === addr.id ? "border-[#e02020] bg-red-50" : "border-gray-100 hover:border-gray-300"}`}>
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-800">
                      <span>{addr.name}</span>
                      <span className="text-gray-500 font-normal">{addr.phoneNumber}</span>
                      {addr.defaultStatus === 1 && <span className="text-xs bg-[#e02020] text-white px-1.5 py-0.5 rounded">默认</span>}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {addr.province}{addr.city}{addr.region} {addr.detailAddress}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Order Items */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h2 className="text-lg font-bold text-gray-900 mb-4">商品明细</h2>
            <div className="space-y-3">
              {cartItems.map((item: ConfirmOrderItem) => (
                <div key={item.id} className="flex items-center gap-4 py-3 border-b border-gray-50 last:border-0">
                  <div className="w-16 h-16 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
                    <img src={item.productPic || "https://images.unsplash.com/photo-1502096472573-eaac515392c6?w=100&q=80"}
                      alt={item.productName} className="w-full h-full object-cover" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-800 line-clamp-1">{item.productName}</p>
                    {item.productSubTitle && <p className="text-xs text-gray-400 mt-0.5">{item.productSubTitle}</p>}
                  </div>
                  <span className="text-sm text-gray-500">x{item.quantity}</span>
                  <span className="text-sm font-medium text-gray-800 w-20 text-right">¥{(item.price * item.quantity).toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Order Note */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h2 className="text-lg font-bold text-gray-900 mb-4">订单备注</h2>
            <textarea value={note} onChange={(e) => setNote(e.target.value)}
              placeholder="选填：如有特殊要求请在此留言..."
              className="w-full p-3 border border-gray-200 rounded-lg text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020]"
            />
          </div>
        </div>

        {/* Right: Price Summary */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl p-6 shadow-sm sticky top-28">
            <h2 className="text-lg font-bold text-gray-900 mb-4">费用明细</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between text-gray-600">
                <span>商品总额</span>
                <span>¥{totalAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>运费</span>
                <span>{amount.freightAmount > 0 ? `¥${amount.freightAmount.toFixed(2)}` : <span className="text-green-600">免运费</span>}</span>
              </div>
              {amount.promotionAmount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>促销优惠</span>
                  <span>-¥{amount.promotionAmount.toFixed(2)}</span>
                </div>
              )}
              <div className="border-t pt-3 flex justify-between text-base font-bold">
                <span>应付总额</span>
                <span className="text-[#e02020]">¥{payAmount.toFixed(2)}</span>
              </div>
            </div>

            {/* Payment Method */}
            <div className="mt-6 pt-4 border-t">
              <h3 className="text-sm font-medium text-gray-700 mb-3">支付方式</h3>
              <div className="grid grid-cols-2 gap-3">
                <label
                  onClick={() => setPayType(1)}
                  className={`flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all ${payType === 1 ? "border-[#e02020] bg-red-50" : "border-gray-200 hover:border-gray-300"}`}
                >
                  <input type="radio" name="payment" checked={payType === 1} readOnly className="accent-[#e02020]" />
                  <span className="text-sm font-medium">支付宝</span>
                </label>
                <label
                  onClick={() => setPayType(2)}
                  className={`flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all ${payType === 2 ? "border-[#e02020] bg-red-50" : "border-gray-200 hover:border-gray-300"}`}
                >
                  <input type="radio" name="payment" checked={payType === 2} readOnly className="accent-[#e02020]" />
                  <span className="text-sm font-medium">微信支付</span>
                </label>
              </div>
            </div>

            <button onClick={handleSubmit} disabled={submitting}
              className="w-full mt-6 bg-[#e02020] text-white py-3 rounded-lg hover:bg-[#c01010] transition-colors font-bold text-base flex items-center justify-center gap-2 disabled:opacity-70">
              {submitting ? <><Loader2 size={18} className="animate-spin" /> 提交中...</> : <>提交订单 ¥{payAmount.toFixed(2)}</>}
            </button>
          </div>
        </div>
      </div>

      {/* Address Modal */}
      {showAddressModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowAddressModal(false)}>
          <div className="bg-white rounded-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <h2 className="text-lg font-bold text-gray-900">新增收货地址</h2>
              <button onClick={() => { setShowAddressModal(false); resetAddressForm() }}
                className="p-1 hover:bg-gray-100 rounded-lg transition-colors">
                <X size={20} className="text-gray-400" />
              </button>
            </div>

            {/* Form */}
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">收货人 <span className="text-red-500">*</span></label>
                  <input value={addressForm.name} onChange={(e) => setAddressForm({ ...addressForm, name: e.target.value })}
                    placeholder="收货人姓名" className="w-full p-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020]" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">手机号码 <span className="text-red-500">*</span></label>
                  <input value={addressForm.phoneNumber} onChange={(e) => setAddressForm({ ...addressForm, phoneNumber: e.target.value })}
                    placeholder="手机号码" className="w-full p-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020]" />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">省份 <span className="text-red-500">*</span></label>
                  <input value={addressForm.province} onChange={(e) => setAddressForm({ ...addressForm, province: e.target.value })}
                    placeholder="省份" className="w-full p-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020]" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">城市 <span className="text-red-500">*</span></label>
                  <input value={addressForm.city} onChange={(e) => setAddressForm({ ...addressForm, city: e.target.value })}
                    placeholder="城市" className="w-full p-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020]" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">区/县 <span className="text-red-500">*</span></label>
                  <input value={addressForm.region} onChange={(e) => setAddressForm({ ...addressForm, region: e.target.value })}
                    placeholder="区/县" className="w-full p-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020]" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">详细地址 <span className="text-red-500">*</span></label>
                <input value={addressForm.detailAddress} onChange={(e) => setAddressForm({ ...addressForm, detailAddress: e.target.value })}
                  placeholder="街道、门牌号等" className="w-full p-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020]" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">邮政编码</label>
                <input value={addressForm.postCode} onChange={(e) => setAddressForm({ ...addressForm, postCode: e.target.value })}
                  placeholder="邮政编码（选填）" className="w-full p-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020]" />
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={addressForm.defaultStatus === 1}
                  onChange={(e) => setAddressForm({ ...addressForm, defaultStatus: e.target.checked ? 1 : 0 })}
                  className="accent-[#e02020] w-4 h-4" />
                <span className="text-sm text-gray-700">设为默认地址</span>
              </label>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-gray-100 flex gap-3">
              <button onClick={() => { setShowAddressModal(false); resetAddressForm() }}
                className="flex-1 py-2.5 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                取消
              </button>
              <button onClick={handleAddAddress} disabled={savingAddress}
                className="flex-1 py-2.5 bg-[#e02020] text-white rounded-lg text-sm font-medium hover:bg-[#c01010] transition-colors disabled:opacity-70 flex items-center justify-center gap-2">
                {savingAddress ? <><Loader2 size={16} className="animate-spin" /> 保存中...</> : "保存"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
