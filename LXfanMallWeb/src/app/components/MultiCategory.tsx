import { useState, useEffect } from "react"
import { Link } from "react-router"
import { ChevronRight, ShoppingCart, Loader2 } from "lucide-react"
import { ImageWithFallback } from "./figma/ImageWithFallback"
import { homeApi, productApi } from "@/utils/api"
import { useCartStore } from "@/store/cartStore"
import { useUserStore } from "@/store/userStore"
import { useAuthModalStore } from "@/store/authModalStore"
import { toast } from "sonner"

function getCategoryEmoji(name: string): string {
  const n = name.toLowerCase()
  if (n.includes("手机") || n.includes("数码")) return "📱"
  if (n.includes("电脑") || n.includes("办公")) return "💻"
  if (n.includes("家电") || n.includes("电器")) return "🏠"
  if (n.includes("服装") || n.includes("服饰") || n.includes("男装") || n.includes("女装")) return "👔"
  if (n.includes("美妆") || n.includes("个护") || n.includes("护肤") || n.includes("彩妆")) return "💄"
  if (n.includes("运动") || n.includes("户外")) return "🏃"
  if (n.includes("食品") || n.includes("生鲜") || n.includes("零食")) return "🍎"
  if (n.includes("图书") || n.includes("音像") || n.includes("书籍")) return "📚"
  if (n.includes("母婴") || n.includes("玩具") || n.includes("童")) return "🧸"
  if (n.includes("家居") || n.includes("家具") || n.includes("装饰")) return "🛋️"
  if (n.includes("鞋") || n.includes("包")) return "👟"
  if (n.includes("汽车")) return "🚗"
  if (n.includes("珠宝") || n.includes("首饰")) return "💎"
  if (n.includes("宠物")) return "🐱"
  if (n.includes("酒") || n.includes("茶")) return "🍷"
  if (n.includes("医药") || n.includes("健康")) return "💊"
  if (n.includes("乐器")) return "🎵"
  return "📁"
}

interface CategoryInfo {
  id: number
  name: string
  icon?: string
  keywords?: string
  level?: number
  parentId?: number
}

const CATEGORY_COLORS = [
  "from-blue-500 to-cyan-400",
  "from-pink-500 to-rose-400",
  "from-amber-500 to-orange-400",
  "from-purple-500 to-violet-400",
  "from-green-500 to-emerald-400",
  "from-red-500 to-orange-400",
  "from-indigo-500 to-blue-400",
  "from-teal-500 to-green-400",
]

export function MultiCategory() {
  const [activeTab, setActiveTab] = useState(0)
  const [hoveredProduct, setHoveredProduct] = useState<number | null>(null)
  const [categories, setCategories] = useState<CategoryInfo[]>([])
  const [categoryProducts, setCategoryProducts] = useState<Record<number, any[]>>({})
  const [loading, setLoading] = useState(true)
  const [loadingProducts, setLoadingProducts] = useState(false)
  const addItem = useCartStore((s) => s.addItem)
  const isAuthenticated = useUserStore((s) => s.isAuthenticated)
  const openAuth = useAuthModalStore((s) => s.openAuth)

  // Fetch top-level categories
  useEffect(() => {
    homeApi.getProductCateList(0)
      .then((data: any) => {
        const list: CategoryInfo[] = Array.isArray(data) ? data : []
        setCategories(list)
        if (list.length > 0) {
          fetchProducts(list[0].id)
        }
      })
      .catch(() => setCategories([]))
      .finally(() => setLoading(false))
  }, [])

  const fetchProducts = (categoryId: number) => {
    if (categoryProducts[categoryId]) return
    setLoadingProducts(true)
    productApi.search({ productCategoryId: categoryId, pageSize: 4, sort: 0 })
      .then((data: any) => {
        const list = data?.list || data?.records || []
        setCategoryProducts((prev) => ({ ...prev, [categoryId]: list }))
      })
      .catch(() => setCategoryProducts((prev) => ({ ...prev, [categoryId]: [] })))
      .finally(() => setLoadingProducts(false))
  }

  const handleTabChange = (index: number) => {
    setActiveTab(index)
    const cat = categories[index]
    if (cat) fetchProducts(cat.id)
  }

  const handleAddToCart = (e: React.MouseEvent, product: any) => {
    e.preventDefault()
    e.stopPropagation()
    if (!isAuthenticated) { toast.error("请先登录"); openAuth("login"); return }
    addItem({
      productId: String(product.id),
      name: product.name || "",
      price: parseFloat(product.price || 0),
      quantity: 1,
      image: product.pic || "",
    })
    toast.success("已加入购物车")
  }

  if (loading) {
    return (
      <div className="max-w-[1440px] mx-auto my-3 px-0">
        <div className="bg-white shadow-sm rounded-sm flex justify-center py-12">
          <Loader2 className="animate-spin text-gray-300" size={32} />
        </div>
      </div>
    )
  }

  if (categories.length === 0) return null

  const currentCategory = categories[activeTab]
  const products = categoryProducts[currentCategory?.id] || []

  return (
    <div className="max-w-[1440px] mx-auto my-3 px-0">
      <div className="bg-white shadow-sm rounded-sm overflow-hidden">
        {/* Section header with tabs */}
        <div className="flex items-center border-b border-gray-100">
          <div className="px-6 py-4 border-r border-gray-100 min-w-[140px]">
            <h2 className="text-xl font-black text-gray-800">多品类好货</h2>
            <p className="text-xs text-gray-400 mt-0.5">精选热门品类</p>
          </div>
          <div className="flex-1 flex overflow-x-auto">
            {categories.map((cat, i) => (
              <button
                key={cat.id}
                onClick={() => handleTabChange(i)}
                className={`flex items-center gap-2 px-5 py-4 text-sm font-medium transition-all duration-200 border-b-2 whitespace-nowrap ${
                  activeTab === i
                    ? "border-[#e02020] text-[#e02020] bg-red-50"
                    : "border-transparent text-gray-600 hover:text-[#e02020] hover:bg-red-50/50"
                }`}
              >
                {cat.name}
              </button>
            ))}
          </div>
          {categories.length > 0 && (
            <Link to={`/category/${currentCategory?.id}`} className="px-6 text-sm text-gray-400 hover:text-[#e02020] flex items-center gap-1 transition-colors whitespace-nowrap">
              查看全部 <ChevronRight size={14} />
            </Link>
          )}
        </div>

        {/* Products */}
        <div className="p-4">
          <div className="grid grid-cols-5 gap-4">
            {/* Category banner */}
            {currentCategory && (
              <Link
                to={`/category/${currentCategory.id}`}
                className={`bg-gradient-to-br ${CATEGORY_COLORS[activeTab % CATEGORY_COLORS.length]} rounded-sm p-5 flex flex-col justify-between text-white min-h-[240px] cursor-pointer hover:shadow-lg transition-shadow`}
              >
                <div>
                  <div className="text-4xl mb-3">{currentCategory.icon || getCategoryEmoji(currentCategory.name)}</div>
                  <h3 className="text-lg font-black">{currentCategory.name}</h3>
                  <p className="text-white/80 text-xs mt-1">{currentCategory.keywords || "精选爆款好货"}</p>
                </div>
                <div>
                  <p className="text-xs text-white/70 mb-2">限时优惠</p>
                  <span className="bg-white/20 hover:bg-white/30 text-white text-xs px-3 py-1.5 rounded-full flex items-center gap-1 transition-colors w-fit">
                    进入专区 <ChevronRight size={12} />
                  </span>
                </div>
              </Link>
            )}

            {/* Products or loading */}
            {loadingProducts ? (
              <div className="col-span-4 flex justify-center items-center">
                <Loader2 className="animate-spin text-gray-300" size={32} />
              </div>
            ) : (
              products.map((product: any) => (
                <Link
                  key={product.id}
                  to={`/product/${product.id}`}
                  className="bg-gray-50 rounded-sm overflow-hidden cursor-pointer group"
                  onMouseEnter={() => setHoveredProduct(product.id)}
                  onMouseLeave={() => setHoveredProduct(null)}
                >
                  <div className="overflow-hidden">
                    <ImageWithFallback
                      src={product.pic || "https://images.unsplash.com/photo-1502096472573-eaac515392c6?w=400&q=80"}
                      alt={product.name}
                      className={`w-full h-44 object-cover transition-transform duration-300 ${
                        hoveredProduct === product.id ? "scale-110" : "scale-100"
                      }`}
                    />
                  </div>
                  <div className="p-3">
                    <div className="text-sm text-gray-700 mb-2 line-clamp-2 h-10 leading-5">
                      {product.name}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[#e02020] font-black">¥{parseFloat(product.price || 0).toFixed(2)}</span>
                      <button
                        onClick={(e) => handleAddToCart(e, product)}
                        className={`p-1.5 rounded-full transition-all duration-200 ${
                          hoveredProduct === product.id
                            ? "bg-[#e02020] text-white scale-110 shadow-md"
                            : "bg-white border border-gray-200 text-gray-400"
                        }`}
                      >
                        <ShoppingCart size={13} />
                      </button>
                    </div>
                  </div>
                </Link>
              ))
            )}

            {/* Fill empty slots if fewer than 4 products */}
            {!loadingProducts && products.length < 4 &&
              Array.from({ length: 4 - products.length }).map((_, i) => (
                <div key={`empty-${i}`} className="bg-gray-50 rounded-sm" />
              ))
            }
          </div>
        </div>
      </div>

      {/* Bottom banner row */}
      <div className="grid grid-cols-3 gap-3 mt-3">
        {[
          {
            bg: "from-red-600 to-red-400",
            title: "品牌直营",
            sub: "正品保障 · 假一赔十",
            img: "https://images.unsplash.com/photo-1607083207685-aaf05f2c908c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=800",
          },
          {
            bg: "from-blue-600 to-blue-400",
            title: "极速配送",
            sub: "当日达 · 次日达",
            img: "https://images.unsplash.com/photo-1647221597996-54f3d0f73809?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=800",
          },
          {
            bg: "from-purple-600 to-purple-400",
            title: "全场无忧",
            sub: "7天退换 · 质量保证",
            img: "https://images.unsplash.com/photo-1763771522867-c26bf75f12bc?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=800",
          },
        ].map((item, i) => (
          <div key={i} className="relative h-28 rounded-sm overflow-hidden cursor-pointer group shadow-sm">
            <ImageWithFallback
              src={item.img}
              alt={item.title}
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
            />
            <div className={`absolute inset-0 bg-gradient-to-r ${item.bg} opacity-80`} />
            <div className="absolute inset-0 flex flex-col justify-center px-6 text-white">
              <h3 className="font-black text-lg">{item.title}</h3>
              <p className="text-white/90 text-xs">{item.sub}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
