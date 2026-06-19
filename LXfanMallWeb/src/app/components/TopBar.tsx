import { useState, useEffect, useRef } from "react"
import { Link, NavLink, useNavigate } from "react-router"
import { ShoppingCart, User, Bell, MapPin, ChevronDown, Heart, Package, LogOut } from "lucide-react"

import { useUserStore } from "@/store/userStore"
import { useCartStore } from "@/store/cartStore"
import { useAuthModalStore } from "@/store/authModalStore"
import { homeApi, cartApi } from "@/utils/api"

interface NavCategory {
  id: number
  name: string
  navStatus?: number
  showStatus?: number
  sort?: number
}

export function TopBar() {
  const { member, isAuthenticated, logout } = useUserStore()
  const cartCount = useCartStore((s) => s.getCount())
  const setCartItems = useCartStore((s) => s.setItems)
  const { openAuth } = useAuthModalStore()
  const [searchKeyword, setSearchKeyword] = useState("")
  const [navCategories, setNavCategories] = useState<NavCategory[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    homeApi.getProductCateList(0)
      .then((data: any) => {
        const list: NavCategory[] = Array.isArray(data) ? data : []
        const navItems = list.filter((c) => c.navStatus === 1)
        setNavCategories(navItems.length > 0 ? navItems : list)
      })
      .catch(() => setNavCategories([]))
  }, [])

  // 登录状态变化时，同步购物车数据
  const prevAuthRef = useRef(isAuthenticated)
  useEffect(() => {
    const justLoggedIn = isAuthenticated && !prevAuthRef.current
    prevAuthRef.current = isAuthenticated

    if (!isAuthenticated) return

    const syncCart = async () => {
      // 刚登录时：清除本地 localStorage 残留的购物车数据，避免脏数据残留
      if (justLoggedIn) {
        useCartStore.getState().clearCart()
        localStorage.removeItem('cart-storage')
      }

      // 从后端拉取完整购物车数据同步到本地 store（用于头部角标）
      const data: any = await cartApi.getList()
      const list = Array.isArray(data) ? data : (data?.list || data?.records || [])
      setCartItems(
        list.map((item: any) => ({
          id: String(item.id),
          productId: String(item.productId),
          name: item.productName || "",
          price: item.price || 0,
          quantity: item.quantity || 0,
          image: item.productPic || "",
        })),
      )
    }

    syncCart().catch(() => {})
  }, [isAuthenticated])

  const handleLogout = () => {
    // 登出前清除本地购物车，防止下一用户登录时合并脏数据
    useCartStore.getState().clearCart()
    logout()
    // 延迟导航，让 logout 状态更新 DOM 先提交，避免与路由切换的 DOM 操作冲突
    setTimeout(() => navigate("/"), 0)
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchKeyword.trim()) {
      navigate(`/category/search?keyword=${encodeURIComponent(searchKeyword.trim())}`)
    }
  }

  return (
    <header className="bg-[#e02020] text-white w-full">
      {/* Top utility bar */}
      <div className="bg-[#c01010]">
        <div className="max-w-[1440px] mx-auto px-6 flex items-center justify-between py-1.5 text-xs">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1 hover:text-yellow-300 cursor-pointer transition-colors">
              <MapPin size={12} /> 北京 <ChevronDown size={10} />
            </span>
            {isAuthenticated ? (
              <>
                <span className="text-white/60">|</span>
                <span className="hover:text-yellow-300 cursor-pointer transition-colors">
                  Hi, {member?.nickname || member?.username || "用户"}
                </span>
                <span className="text-white/60">|</span>
                <span onClick={handleLogout} className="flex items-center gap-1 hover:text-yellow-300 cursor-pointer transition-colors">
                  <LogOut size={12} /> 退出
                </span>
              </>
            ) : (
              <>
                <span className="text-white/60">|</span>
                <span onClick={() => openAuth("login")} className="hover:text-yellow-300 cursor-pointer transition-colors">请登录</span>
                <span onClick={() => openAuth("register")} className="hover:text-yellow-300 cursor-pointer transition-colors">免费注册</span>
              </>
            )}
          </div>
          <div className="flex items-center gap-4">
            <span onClick={() => { if (!isAuthenticated) { openAuth("login"); return } navigate("/orders") }}
              className="flex items-center gap-1 hover:text-yellow-300 cursor-pointer transition-colors">
              <Package size={12} /> 我的订单
            </span>
            <span onClick={() => { if (!isAuthenticated) { openAuth("login"); return } navigate("/profile") }}
              className="flex items-center gap-1 hover:text-yellow-300 cursor-pointer transition-colors">
              <Heart size={12} /> 我的收藏
            </span>
            <span className="flex items-center gap-1 hover:text-yellow-300 cursor-pointer transition-colors">
              <Bell size={12} /> 消息通知
            </span>
            <span className="hover:text-yellow-300 cursor-pointer transition-colors">客服</span>
          </div>
        </div>
      </div>

      {/* Main header */}
      <div className="max-w-[1440px] mx-auto px-6 py-4 flex items-center gap-8">
        <Link to="/" className="flex items-center gap-2 min-w-fit cursor-pointer group">
          <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
            <span className="text-[#e02020] font-black text-sm select-none">LX</span>
          </div>
          <div>
            <div className="text-white font-black text-xl tracking-wide select-none">LXfanMall</div>
            <div className="text-white/70 text-xs select-none">智能购物平台</div>
          </div>
        </Link>

        {/* Search Bar */}
        <form className="flex-1 max-w-2xl" onSubmit={handleSearch}>
          <div className="flex h-10">
            <input
              className="flex-1 px-4 text-sm bg-white placeholder-gray-400 rounded-l-sm focus:outline-none"
              style={{ color: '#1f2937', caretColor: '#1f2937' }}
              placeholder="搜索商品、品牌、店铺..."
              type="text"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
            />
            <button type="submit" className="bg-[#c01010] hover:bg-[#a00000] transition-colors px-6 text-white text-sm font-medium rounded-r-sm whitespace-nowrap">
              搜 索
            </button>
          </div>
          <div className="flex gap-3 mt-1">
            {["iPhone 16 Pro", "耐克运动鞋", "空气炸锅", "连衣裙", "蓝牙耳机"].map((tag) => (
              <span key={tag} onClick={() => { setSearchKeyword(tag); navigate(`/category/search?keyword=${encodeURIComponent(tag)}`) }}
                className="text-white/70 text-xs cursor-pointer hover:text-yellow-300 transition-colors">
                {tag}
              </span>
            ))}
          </div>
        </form>

        {/* Cart & User */}
        <div className="flex items-center gap-6 min-w-fit">
          {isAuthenticated ? (
            <Link to="/profile" className="flex items-center gap-1.5 cursor-pointer hover:text-yellow-300 transition-colors group">
              {member?.icon ? (
                <img src={member.icon} className="w-5 h-5 rounded-full object-cover" alt="" />
              ) : (
                <User size={20} className="group-hover:scale-110 transition-transform" />
              )}
              <span className="text-sm">{member?.nickname || member?.username || "我的账户"}</span>
            </Link>
          ) : (
            <div onClick={() => openAuth("login")} className="flex items-center gap-1.5 cursor-pointer hover:text-yellow-300 transition-colors group">
              <User size={20} className="group-hover:scale-110 transition-transform" />
              <span className="text-sm">我的账户</span>
            </div>
          )}
          <Link to="/cart" className="relative flex items-center gap-1.5 cursor-pointer hover:text-yellow-300 transition-colors group">
            <ShoppingCart size={22} className="group-hover:scale-110 transition-transform" />
            <span className="text-sm">购物车</span>
            {cartCount > 0 && isAuthenticated && (
              <span className="absolute -top-2 -right-3 bg-yellow-400 text-red-800 text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center">
                {cartCount > 99 ? "99+" : cartCount}
              </span>
            )}
          </Link>
        </div>
      </div>

      {/* Navigation bar */}
      <nav className="bg-[#b00000]">
        <div className="max-w-[1440px] mx-auto px-6 flex items-center">
          <NavLink to="/" className={({ isActive }) => `px-4 py-2.5 text-sm text-white transition-colors whitespace-nowrap ${isActive ? "bg-[#e02020]" : "hover:bg-[#e02020]"}`}>
            首页
          </NavLink>
          <NavLink to="/category/seckill" className={({ isActive }) => `px-4 py-2.5 text-sm transition-colors whitespace-nowrap ${isActive ? "bg-[#e02020]" : "hover:bg-[#e02020]"}`}>
            <span className="text-yellow-300 font-medium">秒杀</span>
          </NavLink>
          {navCategories.map((cat) => (
            <NavLink
              key={cat.id}
              to={`/category/${cat.id}`}
              className={({ isActive }) => `px-4 py-2.5 text-sm text-white transition-colors whitespace-nowrap ${isActive ? "bg-[#e02020]" : "hover:bg-[#e02020]"}`}
            >
              {cat.name}
            </NavLink>
          ))}
        </div>
      </nav>

    </header>
  )
}
