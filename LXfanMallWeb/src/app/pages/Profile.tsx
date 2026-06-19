import { useState, useEffect } from "react"
import { Link } from "react-router"
import { useUserStore } from "@/store/userStore"
import { useAuthModalStore } from "@/store/authModalStore"
import { addressApi, collectionApi, historyApi, orderApi } from "@/utils/api"
import { Camera, MapPin, Heart, Clock, Package, Plus, Trash2, ChevronRight, Loader2 } from "lucide-react"
import { toast } from "sonner"

type Tab = "profile" | "orders" | "addresses" | "collections" | "history"

export function Profile() {
  const { member, logout } = useUserStore()
  const openAuth = useAuthModalStore((s) => s.openAuth)
  const [activeTab, setActiveTab] = useState<Tab>("profile")

  const handleLogout = () => {
    logout()
    window.location.href = "/"
  }

  if (!member) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 text-center">
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Camera size={36} className="text-gray-300" />
        </div>
        <p className="text-gray-500 text-lg mb-6">请先登录后查看个人信息</p>
        <button onClick={() => openAuth("login")}
          className="inline-block bg-[#e02020] text-white px-8 py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium">
          立即登录
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8">
      {/* Profile Header */}
      <div className="bg-white rounded-xl p-8 shadow-sm mb-6">
        <div className="flex items-center gap-6">
          <div className="relative">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center overflow-hidden">
              {member.icon ? (
                <img src={member.icon} alt={member.nickname} className="w-full h-full object-cover" />
              ) : (
                <span className="text-2xl font-bold text-[#e02020]">
                  {(member.nickname || member.username)?.[0]?.toUpperCase() || "U"}
                </span>
              )}
            </div>
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900">{member.nickname || member.username}</h2>
            <p className="text-sm text-gray-500 mt-1">
              {member.personalizedSignature || "这个人很懒，什么都没写..."}
            </p>
            <div className="flex items-center gap-4 mt-3 text-sm text-gray-600">
              <span>积分: <span className="text-[#e02020] font-medium">{member.integration || 0}</span></span>
              <span>成长值: <span className="text-[#e02020] font-medium">{member.growth || 0}</span></span>
            </div>
          </div>
          <button onClick={handleLogout}
            className="px-6 py-2 text-sm text-red-500 border border-red-300 rounded-lg hover:bg-red-50 transition-colors">
            退出登录
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-8">
        {/* Sidebar */}
        <div className="w-48 flex-shrink-0">
          <div className="bg-white rounded-xl shadow-sm overflow-hidden sticky top-28">
            {[
              { key: "profile" as Tab, label: "个人信息", icon: Camera },
              { key: "orders" as Tab, label: "我的订单", icon: Package },
              { key: "addresses" as Tab, label: "收货地址", icon: MapPin },
              { key: "collections" as Tab, label: "我的收藏", icon: Heart },
              { key: "history" as Tab, label: "浏览历史", icon: Clock },
            ].map((tab) => (
              <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                className={`w-full flex items-center gap-3 px-5 py-3.5 text-sm transition-colors ${activeTab === tab.key ? "bg-red-50 text-[#e02020] font-medium border-l-3 border-[#e02020]" : "text-gray-600 hover:bg-gray-50 border-l-3 border-transparent"}`}>
                <tab.icon size={18} /> {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {activeTab === "profile" && <ProfileInfo />}
          {activeTab === "orders" && <ProfileOrders />}
          {activeTab === "addresses" && <ProfileAddresses />}
          {activeTab === "collections" && <ProfileCollections />}
          {activeTab === "history" && <ProfileHistory />}
        </div>
      </div>
    </div>
  )
}

function ProfileInfo() {
  const { member } = useUserStore()

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <h3 className="text-lg font-bold text-gray-900 mb-6">个人资料</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InfoField label="用户名" value={member?.username || "-"} />
        <InfoField label="昵称" value={member?.nickname || "-"} />
        <InfoField label="手机号" value={member?.phone || "-"} />
        <InfoField label="性别" value={member?.gender === 1 ? "男" : member?.gender === 2 ? "女" : "保密"} />
        <InfoField label="生日" value={member?.birthday || "-"} />
        <InfoField label="所在城市" value={member?.city || "-"} />
        <InfoField label="职业" value={member?.job || "-"} />
        <InfoField label="会员等级" value={`Lv.${member?.memberLevelId || 1}`} />
        <InfoField label="积分" value={String(member?.integration || 0)} />
        <InfoField label="成长值" value={String(member?.growth || 0)} />
      </div>
    </div>
  )
}

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-sm text-gray-800 font-medium">{value}</p>
    </div>
  )
}

function ProfileOrders() {
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    orderApi.getList({ status: -1, pageNum: 1, pageSize: 5 })
      .then((data: any) => setOrders(data?.list || data?.records || []))
      .catch(() => setOrders([]))
      .finally(() => setLoading(false))
  }, [])

  const statusInfo = (s: number) =>
    ({
      0: { label: "待付款", color: "bg-orange-100 text-orange-600" },
      1: { label: "待发货", color: "bg-blue-100 text-blue-600" },
      2: { label: "已发货", color: "bg-purple-100 text-purple-600" },
      3: { label: "已完成", color: "bg-green-100 text-green-600" },
      4: { label: "已关闭", color: "bg-gray-100 text-gray-500" },
    } as any)[s] || { label: "未知", color: "bg-gray-100 text-gray-500" }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#e02020]" size={32} /></div>

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900">最近订单</h3>
        <Link to="/orders" className="text-sm text-[#e02020] hover:underline flex items-center gap-1">查看全部 <ChevronRight size={14} /></Link>
      </div>
      {orders.length === 0 ? (
        <p className="text-gray-500 text-sm py-8 text-center">暂无订单</p>
      ) : (
        <div className="space-y-3">
          {orders.slice(0, 5).map((order: any) => {
            const s = statusInfo(order.status)
            return (
              <Link key={order.id} to="/orders"
                className="block p-4 border border-gray-100 rounded-lg hover:border-gray-200 hover:shadow-sm transition-all">
                {/* Header */}
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-400">{order.createTime?.slice(0, 10)}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`}>{s.label}</span>
                </div>
                {/* Product preview */}
                {order.orderItemList && order.orderItemList.length > 0 && (
                  <div className="flex items-center gap-2 mb-2">
                    {order.orderItemList.slice(0, 3).map((item: any, idx: number) => (
                      <div key={idx} className="w-12 h-12 rounded-lg overflow-hidden bg-gray-100 border flex-shrink-0">
                        <img src={item.productPic || ""} alt={item.productName} className="w-full h-full object-cover" />
                      </div>
                    ))}
                    <div className="min-w-0 flex-1 ml-1">
                      <p className="text-sm text-gray-800 line-clamp-1">{order.orderItemList[0]?.productName}</p>
                      {order.orderItemList.length > 1 && (
                        <p className="text-xs text-gray-400">等 {order.orderItemList.length} 件商品</p>
                      )}
                    </div>
                  </div>
                )}
                {/* Footer */}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">订单号: {order.orderSn || order.id}</span>
                  <span className="text-sm font-medium text-[#e02020]">¥{parseFloat(String(order.payAmount || order.totalAmount || 0)).toFixed(2)}</span>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}

function ProfileAddresses() {
  const [addresses, setAddresses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const fetchAddresses = () => {
    addressApi.getList()
      .then((data: any) => setAddresses(Array.isArray(data) ? data : (data?.list || data?.records || [])))
      .catch(() => setAddresses([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchAddresses() }, [])

  const handleDelete = (id: number) => {
    if (!confirm("确定删除该地址？")) return
    addressApi.remove(id).then(() => {
      toast.success("地址已删除")
      setAddresses((prev) => prev.filter((a) => a.id !== id))
    }).catch(() => toast.error("删除失败"))
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#e02020]" size={32} /></div>

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900">收货地址</h3>
        <button className="text-sm text-[#e02020] hover:underline flex items-center gap-1"><Plus size={14} /> 添加</button>
      </div>
      {addresses.length === 0 ? (
        <p className="text-gray-500 text-sm py-8 text-center">暂无收货地址</p>
      ) : (
        <div className="space-y-3">
          {addresses.map((addr: any) => (
            <div key={addr.id} className="flex items-start justify-between p-4 border border-gray-100 rounded-lg hover:border-gray-200 transition-colors">
              <div>
                <div className="flex items-center gap-2 text-sm font-medium text-gray-800">
                  <span>{addr.name}</span>
                  <span className="text-gray-500 font-normal">{addr.phoneNumber}</span>
                  {addr.defaultStatus === 1 && <span className="text-xs bg-[#e02020] text-white px-1.5 py-0.5 rounded">默认</span>}
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  {addr.province}{addr.city}{addr.region} {addr.detailAddress}
                </p>
              </div>
              <div className="flex gap-2">
                <button className="text-xs text-gray-400 hover:text-[#e02020] transition-colors">编辑</button>
                <button onClick={() => handleDelete(addr.id)} className="text-xs text-gray-400 hover:text-red-500 transition-colors">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ProfileCollections() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    collectionApi.getList()
      .then((data: any) => setItems(data?.list || data?.records || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [])

  const handleRemove = (productId: number) => {
    collectionApi.remove(productId).then(() => {
      toast.success("已取消收藏")
      setItems((prev) => prev.filter((i) => i.productId !== productId))
    }).catch(() => toast.error("操作失败"))
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#e02020]" size={32} /></div>

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <h3 className="text-lg font-bold text-gray-900 mb-6">我的收藏</h3>
      {items.length === 0 ? (
        <p className="text-gray-500 text-sm py-8 text-center">暂无收藏的商品</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((item: any) => (
            <div key={item.id} className="flex items-center gap-4 p-3 border border-gray-100 rounded-lg hover:border-gray-200 transition-colors">
              <Link to={`/product/${item.productId}`} className="w-16 h-16 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
                <img src={item.productPic || ""} alt={item.productName} className="w-full h-full object-cover" />
              </Link>
              <div className="flex-1 min-w-0">
                <Link to={`/product/${item.productId}`} className="text-sm text-gray-800 line-clamp-1 hover:text-[#e02020] transition-colors">
                  {item.productName}
                </Link>
                <p className="text-sm text-[#e02020] font-medium mt-1">¥{parseFloat(String(item.productPrice || 0)).toFixed(2)}</p>
              </div>
              <button onClick={() => handleRemove(item.productId)}
                className="text-gray-400 hover:text-red-500 transition-colors p-1">
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ProfileHistory() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    historyApi.getList()
      .then((data: any) => setItems(data?.list || data?.records || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [])

  const handleClear = () => {
    if (!confirm("确定清空浏览历史？")) return
    historyApi.clear().then(() => {
      toast.success("已清空")
      setItems([])
    }).catch(() => toast.error("操作失败"))
  }

  const handleDelete = (ids: string[]) => {
    historyApi.remove(ids).then(() => {
      toast.success("已删除")
      setItems((prev) => prev.filter((i) => !ids.includes(String(i.id))))
    }).catch(() => toast.error("删除失败"))
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#e02020]" size={32} /></div>

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900">浏览历史</h3>
        {items.length > 0 && (
          <button onClick={handleClear} className="text-sm text-gray-500 hover:text-red-500 transition-colors">清空全部</button>
        )}
      </div>
      {items.length === 0 ? (
        <p className="text-gray-500 text-sm py-8 text-center">暂无浏览记录</p>
      ) : (
        <div className="space-y-2">
          {items.map((item: any) => (
            <div key={item.id} className="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-lg transition-colors">
              <Link to={`/product/${item.productId}`} className="w-14 h-14 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
                <img src={item.productPic || ""} alt={item.productName} className="w-full h-full object-cover" />
              </Link>
              <div className="flex-1 min-w-0">
                <Link to={`/product/${item.productId}`} className="text-sm text-gray-800 line-clamp-1 hover:text-[#e02020] transition-colors">
                  {item.productName}
                </Link>
                <p className="text-xs text-gray-400 mt-0.5">{item.createTime}</p>
              </div>
              <span className="text-sm text-[#e02020] font-medium">¥{parseFloat(String(item.productPrice || 0)).toFixed(2)}</span>
              <button onClick={() => handleDelete([String(item.id)])}
                className="text-gray-400 hover:text-red-500 transition-colors p-1 ml-2">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
