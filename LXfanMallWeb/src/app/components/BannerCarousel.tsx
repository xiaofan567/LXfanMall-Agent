import { useState, useEffect, useCallback } from "react"
import { Link } from "react-router"
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react"
import { ImageWithFallback } from "./figma/ImageWithFallback"
import { homeApi } from "@/utils/api"

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

const BANNERS = [
  {
    id: 1,
    image: "https://images.unsplash.com/photo-1607083207685-aaf05f2c908c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxlY29tbWVyY2UlMjBzaG9wcGluZyUyMHNhbGUlMjBiYW5uZXIlMjByZWR8ZW58MXx8fHwxNzc4NTg5MzA3fDA&ixlib=rb-4.1.0&q=80&w=1080",
    title: "年中大促 全场五折起",
    subtitle: "数千品牌 限时狂欢",
    badge: "限时特惠",
    color: "from-red-900/80 to-transparent",
  },
  {
    id: 2,
    image: "https://images.unsplash.com/photo-1647221597996-54f3d0f73809?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxvbmxpbmUlMjBzaG9wcGluZyUyMGRpc2NvdW50JTIwc2FsZSUyMHByb21vdGlvbnxlbnwxfHx8fDE3Nzg1ODkzMTJ8MA&ixlib=rb-4.1.0&q=80&w=1080",
    title: "超值爆款 每日精选",
    subtitle: "AI智能推荐 专属好货",
    badge: "AI推荐",
    color: "from-blue-900/80 to-transparent",
  },
  {
    id: 3,
    image: "https://images.unsplash.com/photo-1763771522867-c26bf75f12bc?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwY2xvdGhpbmclMjBhcHBhcmVsJTIwc3RvcmV8ZW58MXx8fHwxNzc4NTg5MzA4fDA&ixlib=rb-4.1.0&q=80&w=1080",
    title: "时尚新品 潮流上新",
    subtitle: "大牌云集 品质保障",
    badge: "新品首发",
    color: "from-purple-900/80 to-transparent",
  },
]

interface BannerAd {
  id: number
  pic?: string
  name?: string
  note?: string
  url?: string
}

interface CategoryItem {
  id: number
  parentId: number
  name: string
  level: number
  icon?: string
  keywords?: string
  navStatus?: number
  showStatus?: number
  sort?: number
}

export function BannerCarousel({ ads }: { ads?: BannerAd[] }) {
  const [current, setCurrent] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [hoveredCategory, setHoveredCategory] = useState<number | null>(null)
  const [categories, setCategories] = useState<CategoryItem[]>([])
  const [subCategories, setSubCategories] = useState<Record<number, CategoryItem[]>>({})
  const [loadingSub, setLoadingSub] = useState<number | null>(null)

  // 使用数据库广告，没有则用默认
  const bannerList = Array.isArray(ads) && ads.length > 0
    ? ads.map((ad) => ({
        id: ad.id,
        image: ad.pic || "",
        title: ad.name || "限时活动",
        subtitle: ad.note || "精选好物",
        badge: "活动",
        color: "from-gray-900/70 to-transparent",
        url: ad.url,
      }))
    : BANNERS

  const handleBannerClick = (banner: typeof bannerList[0]) => {
    const url = banner.url
    if (!url) { window.location.href = '/activity-coming-soon'; return }
    if (url.startsWith('http://') || url.startsWith('https://')) {
      window.open(url, '_blank', 'noopener')
    } else if (url.startsWith('/')) {
      window.location.href = url
    } else {
      window.location.href = '/activity-coming-soon'
    }
  }

  useEffect(() => {
    homeApi.getProductCateList(0)
      .then((data: any) => {
        const list: CategoryItem[] = Array.isArray(data) ? data : []
        setCategories(list)
      })
      .catch(() => setCategories([]))
  }, [])

  const handleHover = (catId: number) => {
    setHoveredCategory(catId)
    if (!subCategories[catId]) {
      setLoadingSub(catId)
      homeApi.getProductCateList(catId)
        .then((data: any) => {
          const list: CategoryItem[] = Array.isArray(data) ? data : []
          setSubCategories((prev) => ({ ...prev, [catId]: list }))
        })
        .catch(() => setSubCategories((prev) => ({ ...prev, [catId]: [] })))
        .finally(() => setLoadingSub(null))
    }
  }

  const goTo = useCallback(
    (index: number) => {
      if (isTransitioning) return
      setIsTransitioning(true)
      setCurrent((index + bannerList.length) % bannerList.length)
      setTimeout(() => setIsTransitioning(false), 500)
    },
    [isTransitioning, bannerList.length]
  )

  useEffect(() => {
    const timer = setInterval(() => goTo(current + 1), 4000)
    return () => clearInterval(timer)
  }, [current, goTo])

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-3">
      <div className="flex gap-3">
        {/* Left category menu */}
        <div className="w-[200px] shrink-0 bg-white shadow-sm rounded-sm relative z-20">
          {categories.length === 0 ? (
            <div className="flex justify-center py-8">
              <Loader2 className="animate-spin text-gray-300" size={24} />
            </div>
          ) : (
            categories.map((cat) => (
              <div
                key={cat.id}
                className="group relative"
                onMouseEnter={() => handleHover(cat.id)}
                onMouseLeave={() => { setHoveredCategory(null); setLoadingSub(null) }}
              >
                <Link
                  to={`/category/${cat.id}`}
                  className={`flex items-center gap-2.5 px-4 py-2.5 cursor-pointer transition-all duration-200 ${
                    hoveredCategory === cat.id
                      ? "bg-[#e02020] text-white"
                      : "hover:bg-red-50 text-gray-700"
                  }`}
                >
                  <span className="text-base">{cat.icon || getCategoryEmoji(cat.name)}</span>
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{cat.name}</div>
                    <div className={`text-xs truncate ${hoveredCategory === cat.id ? "text-white/80" : "text-gray-400"}`}>
                      {cat.keywords || "精选好物"}
                    </div>
                  </div>
                  <ChevronRight
                    size={12}
                    className={`ml-auto shrink-0 ${hoveredCategory === cat.id ? "text-white" : "text-gray-300"}`}
                  />
                </Link>

                {/* Dropdown flyout */}
                {hoveredCategory === cat.id && (
                  <div
                    className="absolute left-[200px] top-0 w-[500px] bg-white shadow-2xl border border-gray-100 rounded-r-sm p-4 z-50 min-h-[200px]"
                    style={{ animation: "fadeInLeft 0.15s ease" }}
                  >
                    <div className="text-sm font-semibold text-[#e02020] mb-3 border-b border-red-100 pb-2">
                      {cat.name} 全部分类
                    </div>
                    {loadingSub === cat.id ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="animate-spin text-gray-300" size={20} />
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-1">
                        {(subCategories[cat.id] || []).length > 0 ? (
                          subCategories[cat.id].map((sub) => (
                            <Link
                              key={sub.id}
                              to={`/category/${sub.id}`}
                              className="text-xs text-gray-600 hover:text-[#e02020] cursor-pointer py-1.5 px-2 hover:bg-red-50 rounded transition-colors truncate"
                            >
                              {sub.name}
                            </Link>
                          ))
                        ) : (
                          <div className="col-span-3 text-xs text-gray-400 py-8 text-center">暂无子分类</div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Banner carousel */}
        <div className="flex-1 relative overflow-hidden rounded-sm" style={{ height: "340px" }}>
          {bannerList.map((banner, i) => (
            <div
              key={banner.id}
              onClick={() => handleBannerClick(banner)}
              className={`absolute inset-0 transition-all duration-500 ease-in-out cursor-pointer ${
                i === current ? "opacity-100 scale-100 z-10" : "opacity-0 scale-105 z-0 pointer-events-none"
              }`}
            >
              <ImageWithFallback
                src={banner.image}
                alt={banner.title}
                className="w-full h-full object-cover"
              />
              <div className={`absolute inset-0 bg-gradient-to-r ${banner.color} pointer-events-none`} />
              <div className="absolute bottom-8 left-8 text-white pointer-events-none">
                <span className="inline-block bg-[#e02020] text-white text-xs px-3 py-1 rounded-full mb-3 animate-pulse">
                  {banner.badge}
                </span>
                <h2 className="text-3xl font-black mb-1 drop-shadow-lg">{banner.title}</h2>
                <p className="text-white/90 text-base mb-4 drop-shadow">{banner.subtitle}</p>
                <span className="inline-block bg-[#e02020] hover:bg-[#c01010] text-white px-6 py-2 rounded-sm text-sm font-medium transition-all duration-200 hover:scale-105 shadow-lg">
                  立即查看
                </span>
              </div>
            </div>
          ))}

          {/* Controls */}
          <button
            onClick={() => goTo(current - 1)}
            className="absolute left-3 top-1/2 -translate-y-1/2 w-8 h-8 bg-black/30 hover:bg-black/60 text-white rounded-full flex items-center justify-center transition-all opacity-0 hover:opacity-100 group-hover:opacity-100 z-10"
            style={{ opacity: 0.7 }}
          >
            <ChevronLeft size={16} />
          </button>
          <button
            onClick={() => goTo(current + 1)}
            className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 bg-black/30 hover:bg-black/60 text-white rounded-full flex items-center justify-center transition-all z-10"
            style={{ opacity: 0.7 }}
          >
            <ChevronRight size={16} />
          </button>

          {/* Dots */}
          <div className="absolute bottom-3 right-4 flex gap-1.5 z-10">
            {bannerList.map((_, i) => (
              <button
                key={i}
                onClick={() => goTo(i)}
                className={`transition-all duration-300 rounded-full ${
                  i === current ? "w-6 h-2 bg-white" : "w-2 h-2 bg-white/50 hover:bg-white/80"
                }`}
              />
            ))}
          </div>
        </div>

        {/* Right sidebar ads */}
        <div className="w-[150px] shrink-0 flex flex-col gap-2">
          <div className="bg-gradient-to-br from-orange-400 to-red-500 rounded-sm p-3 text-white cursor-pointer hover:shadow-lg transition-shadow flex-1 flex flex-col justify-between">
            <div className="text-xs font-medium">新人专享</div>
            <div className="text-lg font-black">¥50</div>
            <div className="text-xs opacity-80">优惠券</div>
          </div>
          <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-sm p-3 text-white cursor-pointer hover:shadow-lg transition-shadow flex-1 flex flex-col justify-between">
            <div className="text-xs font-medium">每日签到</div>
            <div className="text-lg font-black">+积分</div>
            <div className="text-xs opacity-80">赚好礼</div>
          </div>
          <div className="bg-gradient-to-br from-blue-500 to-cyan-500 rounded-sm p-3 text-white cursor-pointer hover:shadow-lg transition-shadow flex-1 flex flex-col justify-between">
            <div className="text-xs font-medium">闪电直播</div>
            <div className="text-lg font-black">进行中</div>
            <div className="text-xs opacity-80">超低价</div>
          </div>
        </div>
      </div>
    </div>
  )
}
