import { Link } from "react-router"
import { useCartStore } from "@/store/cartStore"
import { useUserStore } from "@/store/userStore"
import { useAuthModalStore } from "@/store/authModalStore"
import { cartApi } from "@/utils/api"
import { useEffect, useState } from "react"
import { Minus, Plus, Trash2, ShoppingBag, Loader2 } from "lucide-react"
import { toast } from "sonner"

interface CartProduct {
  id: number
  productId: number
  productName: string
  productPic: string
  price: number
  quantity: number
  productSubTitle?: string
  productSkuId?: number
  productAttr?: string
}

export function Cart() {
  const [items, setItems] = useState<CartProduct[]>([])
  const [loading, setLoading] = useState(true)
  const clearCartStore = useCartStore((s) => s.clearCart)
  const setCartItems = useCartStore((s) => s.setItems)
  const isAuthenticated = useUserStore((s) => s.isAuthenticated)
  const openAuth = useAuthModalStore((s) => s.openAuth)

  /** 同步后端购物车数据到本地 store（用于头部角标） */
  const syncToLocalStore = (list: CartProduct[]) => {
    setCartItems(
      list.map((item: any) => ({
        id: String(item.id),
        productId: String(item.productId),
        name: item.productName || "",
        price: item.price || 0,
        quantity: item.quantity || 0,
        image: item.productPic || "",
      }))
    )
  }

  const fetchCart = () => {
    setLoading(true)
    cartApi.getList()
      .then((data: any) => {
        const list = Array.isArray(data) ? data : (data?.list || data?.records || [])
        setItems(list)
        syncToLocalStore(list)
      })
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false)
      return
    }
    fetchCart()
  }, [])

  const handleQuantityChange = (id: number, newQty: number) => {
    if (newQty < 1) return
    cartApi.updateQuantity(id, newQty).then(() => {
      const updated = items.map((i) => (i.id === id ? { ...i, quantity: newQty } : i))
      setItems(updated)
      syncToLocalStore(updated)
    }).catch(() => toast.error("修改数量失败"))
  }

  const handleRemove = (id: number) => {
    cartApi.remove([id]).then(() => {
      const updated = items.filter((i) => i.id !== id)
      setItems(updated)
      syncToLocalStore(updated)
      toast.success("已移除")
    }).catch(() => toast.error("删除失败"))
  }

  const handleClear = () => {
    cartApi.clear().then(() => {
      setItems([])
      clearCartStore()
      toast.success("购物车已清空")
    }).catch(() => toast.error("清空失败"))
  }

  const total = items.reduce((sum, i) => sum + i.price * i.quantity, 0)

  if (loading) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 flex justify-center">
        <Loader2 className="animate-spin text-[#e02020]" size={48} />
      </div>
    )
  }

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">我的购物车</h1>
      <p className="text-sm text-gray-500 mb-8">共 {items.length} 件商品</p>

      {items.length === 0 ? (
        <div className="bg-white rounded-xl p-16 text-center shadow-sm">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <ShoppingBag size={36} className="text-gray-300" />
          </div>
          {isAuthenticated ? (
            <>
              <p className="text-gray-500 text-lg mb-6">购物车还是空的</p>
              <Link to="/" className="inline-block bg-[#e02020] text-white px-8 py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium">
                去逛逛
              </Link>
            </>
          ) : (
            <>
              <p className="text-gray-500 text-lg mb-4">请先登录后再查看购物车</p>
              <p className="text-gray-400 text-sm mb-6">登录后可同步您的购物车商品</p>
              <button onClick={() => openAuth("login")} className="inline-block bg-[#e02020] text-white px-8 py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium cursor-pointer">
                去登录
              </button>
            </>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="flex items-center justify-between px-6 py-3 bg-gray-50 text-sm text-gray-600">
                <span>商品信息</span>
                <div className="flex items-center gap-16">
                  <span>单价</span>
                  <span>数量</span>
                  <span className="w-16 text-right">小计</span>
                  <span className="w-10"></span>
                </div>
              </div>
              {items.map((item) => (
                <div key={item.id} className="flex items-center justify-between px-6 py-4 border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <Link to={`/product/${item.productId}`} className="w-20 h-20 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
                      <img src={item.productPic || "https://images.unsplash.com/photo-1502096472573-eaac515392c6?w=200&q=80"}
                        alt={item.productName} className="w-full h-full object-cover" />
                    </Link>
                    <div className="min-w-0">
                      <Link to={`/product/${item.productId}`} className="text-sm text-gray-800 line-clamp-2 hover:text-[#e02020] transition-colors">
                        {item.productName}
                      </Link>
                      {item.productSubTitle && <p className="text-xs text-gray-400 mt-1">{item.productSubTitle}</p>}
                      {item.productAttr && (
                        <p className="text-xs text-gray-400 mt-1">{item.productAttr}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-16 text-sm">
                    <span className="text-gray-700 font-medium">¥{(item.price ?? 0).toFixed(2)}</span>
                    <div className="flex items-center border rounded-lg">
                      <button onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                        className="p-1.5 hover:bg-gray-100 transition-colors"><Minus size={14} /></button>
                      <span className="w-10 text-center font-medium">{item.quantity}</span>
                      <button onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                        className="p-1.5 hover:bg-gray-100 transition-colors"><Plus size={14} /></button>
                    </div>
                    <span className="text-[#e02020] font-bold w-16 text-right">¥{(item.price * item.quantity).toFixed(2)}</span>
                    <button onClick={() => handleRemove(item.id)} className="w-10 flex justify-center text-gray-400 hover:text-red-500 transition-colors">
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <button onClick={handleClear} className="text-sm text-gray-500 hover:text-red-500 transition-colors">
              清空购物车
            </button>
          </div>

          {/* Order Summary Sidebar */}
          <div className="bg-white rounded-xl p-6 shadow-sm h-fit sticky top-28">
            <h2 className="text-lg font-bold text-gray-900 mb-1">订单摘要</h2>
            <p className="text-xs text-gray-400 mb-4">已选 {items.length} 件商品</p>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between text-gray-600">
                <span>商品总额</span>
                <span>¥{total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>运费</span>
                <span className="text-green-600">免运费</span>
              </div>
              <div className="border-t pt-3 flex justify-between text-base font-bold">
                <span>应付总额</span>
                <span className="text-[#e02020]">¥{total.toFixed(2)}</span>
              </div>
            </div>
            <button onClick={() => {
                if (!isAuthenticated) { toast.error("请先登录"); openAuth("login"); return }
                window.location.href = "/order"
              }}
              className="block w-full bg-[#e02020] text-white text-center py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium mt-6">
              去结算
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
