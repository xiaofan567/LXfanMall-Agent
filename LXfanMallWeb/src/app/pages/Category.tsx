import { useParams, useNavigate, useSearchParams } from "react-router"
import { PackageOpen, ShoppingCart, Heart, Filter, Loader2, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react"
import { useEffect, useState, useRef } from "react"
import { productApi, cartApi, homeApi, collectionApi, searchApi_es } from "@/utils/api"
import { useCartStore } from "@/store/cartStore"
import { useUserStore } from "@/store/userStore"
import { useAuthModalStore } from "@/store/authModalStore"
import { toast } from "sonner"

interface CatNode {
  id: number
  name: string
  parentId: number
  level: number
  children?: CatNode[]
}

export function Category() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const addItem = useCartStore((s) => s.addItem)
  const isAuthenticated = useUserStore((s) => s.isAuthenticated)
  const openAuth = useAuthModalStore((s) => s.openAuth)
  const [products, setProducts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [title, setTitle] = useState("分类")
  const [sort, setSort] = useState(0)
  const [pageNum, setPageNum] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPage, setTotalPage] = useState(0)
  const [subCategories, setSubCategories] = useState<CatNode[]>([])
  const [currentParentId, setCurrentParentId] = useState<number | null>(null)
  const catMapRef = useRef<Record<number, CatNode>>({})

  // 收藏状态
  const [collectedIds, setCollectedIds] = useState<Set<number>>(new Set())

  // 加载收藏列表
  useEffect(() => {
    if (!isAuthenticated) return
    collectionApi.getList(1, 100)
      .then((data: any) => {
        const list = data?.list || data?.records || []
        setCollectedIds(new Set(list.map((item: any) => item.productId)))
      })
      .catch(() => {})
  }, [isAuthenticated])

  const isSearch = id === "search"
  const keyword = isSearch ? (searchParams.get("keyword") || "") : ""
  const isNumeric = id && /^\d+$/.test(id)
  const categoryId = isNumeric ? parseInt(id!) : undefined

  // Legacy slug mapping for backward compatibility
  const legacySlugMap: Record<string, number> = {
    "digital": 29, "computer": 31, "appliances": 33, "fashion": 35,
    "beauty": 34, "sports": 36, "fresh": 37, "books": 38, "toys": 39, "furniture": 40,
  }
  const legacySlugNames: Record<string, string> = {
    "seckill": "秒杀", "digital": "手机数码", "computer": "电脑办公",
    "appliances": "家用电器", "fashion": "服装服饰", "beauty": "美妆个护",
    "sports": "运动户外", "fresh": "食品生鲜", "books": "图书音像",
    "toys": "母婴玩具", "furniture": "家居家具",
  }

  // Build a complete ID→name map from all category levels
  const buildCategoryMap = async () => {
    try {
      const topData: any = await homeApi.getProductCateList(0)
      const topList: any[] = Array.isArray(topData) ? topData : []
      const map: Record<number, CatNode> = {}

      const childResults = await Promise.allSettled(
        topList.map((cat: any) => homeApi.getProductCateList(cat.id))
      )

      topList.forEach((cat: any, i: number) => {
        const children: any[] =
          childResults[i].status === "fulfilled"
            ? (Array.isArray((childResults[i] as any).value) ? (childResults[i] as any).value : [])
            : []
        map[cat.id] = {
          id: cat.id,
          name: cat.name,
          parentId: 0,
          level: cat.level ?? 0,
          children: children.map((c: any) => ({
            id: c.id,
            name: c.name,
            parentId: cat.id,
            level: c.level ?? 1,
          })),
        }
        children.forEach((c: any) => {
          map[c.id] = { id: c.id, name: c.name, parentId: cat.id, level: c.level ?? 1 }
        })
      })

      catMapRef.current = map
      return map
    } catch {
      return catMapRef.current
    }
  }

  // 排序或搜索词变化时重置页码
  useEffect(() => {
    setPageNum(1)
  }, [sort, keyword])

  useEffect(() => {
    if (!id) return
    setLoading(true)

    const resolveCategory = async () => {
      let map = catMapRef.current
      if (Object.keys(map).length === 0) {
        map = await buildCategoryMap()
      }

      let effectiveCategoryId: number | undefined
      let displayTitle = "分类"

      if (isSearch) {
        displayTitle = `搜索: "${keyword}"`
      } else if (isNumeric) {
        effectiveCategoryId = categoryId
        const found = map[categoryId!]
        if (found) {
          if (found.children && found.children.length > 0) {
            // Top-level with children → show children as pills, title stays as parent
            setSubCategories(found.children)
            setCurrentParentId(found.id)
            displayTitle = found.name
          } else if (found.parentId && found.parentId > 0) {
            // Subcategory → show siblings, title uses PARENT name
            const parent = map[found.parentId]
            if (parent) {
              displayTitle = parent.name
              setSubCategories(parent.children || [])
              setCurrentParentId(parent.id)
            } else {
              displayTitle = found.name
              setSubCategories([])
              setCurrentParentId(null)
              }
          } else {
            // Top-level without children
            displayTitle = found.name
            setSubCategories([])
            setCurrentParentId(null)
          }
        } else {
          setSubCategories([])
          setCurrentParentId(null)
        }
      } else if (id && legacySlugMap[id]) {
        effectiveCategoryId = legacySlugMap[id]
        displayTitle = legacySlugNames[id] || id
        const found = map[effectiveCategoryId]
        if (found?.children) {
          setSubCategories(found.children)
          setCurrentParentId(found.id)
        } else {
          setSubCategories([])
          setCurrentParentId(null)
        }
      }

      setTitle(displayTitle)

      // Search: if parent has children, also fetch child category products
      const currentCat = effectiveCategoryId ? map[effectiveCategoryId] : null
      const childIds = currentCat?.children?.map((c) => c.id) || []

      if (childIds.length > 0) {
        // Parallel search: parent + all children
        const allIds = [effectiveCategoryId!, ...childIds]
        try {
          const results = await Promise.allSettled(
            allIds.map((cid) =>
              productApi.search({ productCategoryId: cid, pageNum: 1, pageSize: 20, sort })
            )
          )
          const merged: any[] = []
          const seen = new Set<number>()
          results.forEach((r) => {
            if (r.status === "fulfilled") {
              const list = (r.value as any)?.list || (r.value as any)?.records || []
              list.forEach((p: any) => {
                if (!seen.has(p.id)) {
                  seen.add(p.id)
                  merged.push(p)
                }
              })
            }
          })
          setProducts(merged)
        } catch {
          setProducts([])
        } finally {
          setLoading(false)
        }
      } else if (effectiveCategoryId) {
        // No children, simple search
        const params: any = { productCategoryId: effectiveCategoryId, pageNum, pageSize: 20, sort }
        try {
          const data: any = await productApi.search(params)
          setProducts(data?.list || data?.records || [])
        } catch {
          setProducts([])
        } finally {
          setLoading(false)
        }
      } else if (isSearch && keyword) {
        // Keyword search — 使用 Elasticsearch
        try {
          const data: any = await searchApi_es.search({ keyword, pageNum: pageNum - 1, pageSize: 20, sort })
          setProducts(data?.list || [])
          setTotal(data?.total || 0)
          setTotalPage(data?.totalPage || 0)
        } catch {
          setProducts([])
          setTotal(0)
          setTotalPage(0)
        } finally {
          setLoading(false)
        }
      } else if (id === "all") {
        // 全部商品
        displayTitle = "全部商品"
        try {
          const data: any = await productApi.search({ pageNum: 1, pageSize: 20, sort })
          setProducts(data?.list || data?.records || [])
        } catch {
          setProducts([])
        } finally {
          setLoading(false)
        }
      } else {
        setProducts([])
        setLoading(false)
      }
    }

    resolveCategory()
  }, [id, sort, pageNum, keyword])

  const handleAddToCart = async (e: React.MouseEvent, product: any) => {
    e.stopPropagation()
    if (!isAuthenticated) { toast.error("请先登录"); openAuth("login"); return }

    // 检查商品是否有规格，有则跳转到详情页让用户选择规格
    try {
      const detail: any = await productApi.getDetail(product.id)
      const attrs = detail?.productAttributeList || []
      if (attrs.length > 0) {
        toast.info("请选择商品规格后再加入购物车")
        navigate(`/product/${product.id}`)
        return
      }
    } catch {
      // 获取详情失败，直接添加
    }

    cartApi.add({ productId: product.id, quantity: 1 }).catch(() => {})
    addItem({
      productId: String(product.id),
      name: product.name || "",
      price: parseFloat(product.price || 0),
      quantity: 1,
      image: product.pic || product.albumPics || "",
    })
    toast.success("已加入购物车")
  }

  const handleToggleCollection = async (e: React.MouseEvent, productId: number) => {
    e.stopPropagation()
    if (!isAuthenticated) { toast.error("请先登录"); openAuth("login"); return }

    const isCollected = collectedIds.has(productId)
    try {
      if (isCollected) {
        await collectionApi.remove(productId)
        setCollectedIds((prev) => { const next = new Set(prev); next.delete(productId); return next })
        toast.success("已取消收藏")
      } else {
        await collectionApi.add(productId)
        setCollectedIds((prev) => { const next = new Set(prev); next.add(productId); return next })
        toast.success("已收藏")
      }
    } catch {
      toast.error(isCollected ? "取消收藏失败" : "收藏失败")
    }
  }

  return (
    <main className="max-w-[1440px] mx-auto px-6 py-8 min-h-[60vh]">
      {/* Header */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-4 flex items-center justify-between border border-gray-100">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center">
            <PackageOpen size={24} className="text-[#e02020]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              {title}
              <span className="text-base font-normal text-gray-400 ml-1">频道</span>
            </h1>
            <p className="text-gray-500 text-sm mt-1">为您精选优质好物，每日上新，品质保障</p>
          </div>
        </div>
      </div>

      {/* Subcategory navigation pills */}
      {subCategories.length > 0 && (
        <div className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-gray-500 mr-2">分类:</span>
            {/* "全部" pill — always visible when there are subcategories */}
            <button
              onClick={() => navigate(`/category/${currentParentId}`)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                categoryId === currentParentId
                  ? "bg-[#e02020] text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              全部
            </button>
            {subCategories.map((sub) => (
              <button
                key={sub.id}
                onClick={() => navigate(`/category/${sub.id}`)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  categoryId === sub.id
                    ? "bg-[#e02020] text-white"
                    : "bg-gray-50 text-gray-600 hover:bg-red-50 hover:text-[#e02020]"
                }`}
              >
                {sub.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-white rounded-xl p-4 shadow-sm mb-6 flex items-center justify-between text-sm text-gray-600 border border-gray-100">
        <div className="flex gap-8">
          {[
            { label: "综合排序", value: 0 },
            { label: "销量优先", value: 2 },
            { label: "价格升序", value: 3 },
            { label: "价格降序", value: 4 },
            { label: "新品优先", value: 1 },
          ].map((item) => (
            <button key={item.value} onClick={() => setSort(item.value)}
              className={`cursor-pointer transition-colors ${sort === item.value ? "font-medium text-[#e02020]" : "hover:text-[#e02020]"}`}>
              {item.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 px-3 py-1 bg-gray-50 rounded-md">
          <Filter size={16} /> 更多筛选
        </div>
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#e02020]" size={40} /></div>
      ) : products.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <PackageOpen size={48} className="mx-auto mb-4 opacity-40" />
          <p className="text-lg">该分类暂无商品</p>
          <p className="text-sm mt-2">商品正在上架中，请稍后再来</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {products.map((product: any) => (
            <div key={product.id} onClick={() => navigate(`/product/${product.id}`)}
              className="bg-white rounded-xl overflow-hidden hover:shadow-xl transition-all duration-300 group cursor-pointer border border-transparent hover:border-[#e02020]/30">
              <div className="relative aspect-square overflow-hidden bg-gray-50">
                <img src={product.pic || product.albumPics || "https://images.unsplash.com/photo-1502096472573-eaac515392c6?w=500&q=80"}
                  alt={product.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                {product.newStatus === 1 && (
                  <div className="absolute top-2 left-2 bg-[#e02020] text-white text-[10px] px-2 py-0.5 rounded-sm font-medium z-10">新品</div>
                )}
                <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center gap-3">
                  <button onClick={(e) => handleToggleCollection(e, product.id)}
                    className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors shadow-lg ${
                      collectedIds.has(product.id)
                        ? "bg-white text-[#e02020]"
                        : "bg-white text-gray-700 hover:bg-[#e02020] hover:text-white"
                    }`}>
                    <Heart size={18} className={collectedIds.has(product.id) ? "fill-[#e02020] text-[#e02020]" : ""} />
                  </button>
                  <button onClick={(e) => handleAddToCart(e, product)}
                    className="w-10 h-10 bg-[#e02020] rounded-full flex items-center justify-center text-white hover:bg-[#c01010] transition-colors shadow-lg">
                    <ShoppingCart size={18} />
                  </button>
                </div>
              </div>
              <div className="p-4">
                <div className="text-xl font-bold text-[#e02020] mb-2 flex items-baseline gap-1">
                  <span className="text-sm">¥</span>
                  {parseFloat(product.price || 0).toFixed(2)}
                  {product.originalPrice && (
                    <span className="text-xs text-gray-400 line-through font-normal ml-1">¥{parseFloat(product.originalPrice).toFixed(2)}</span>
                  )}
                </div>
                <h3 className="text-sm text-gray-800 line-clamp-2 leading-snug h-[40px] group-hover:text-[#e02020] transition-colors">
                  {product.name || product.productName}
                </h3>
                <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
                  <span>{product.sale || 0}条评价</span>
                  <span className="text-[#e02020] bg-red-50 px-1.5 py-0.5 rounded text-[10px]">自营</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination — 仅搜索模式显示 */}
      {isSearch && !loading && totalPage > 1 && (
        <div className="mt-8 flex items-center justify-center gap-4">
          <span className="text-sm text-gray-500 mr-2">共 {total} 条结果</span>
          <button
            onClick={() => setPageNum(1)}
            disabled={pageNum <= 1}
            className="p-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronsLeft size={16} />
          </button>
          <button
            onClick={() => setPageNum((p) => Math.max(1, p - 1))}
            disabled={pageNum <= 1}
            className="p-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm text-gray-700 min-w-[80px] text-center">
            第 {pageNum}/{totalPage} 页
          </span>
          <button
            onClick={() => setPageNum((p) => Math.min(totalPage, p + 1))}
            disabled={pageNum >= totalPage}
            className="p-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight size={16} />
          </button>
          <button
            onClick={() => setPageNum(totalPage)}
            disabled={pageNum >= totalPage}
            className="p-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronsRight size={16} />
          </button>
        </div>
      )}
    </main>
  )
}
