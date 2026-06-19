import { useParams, Link } from "react-router"
import { useCartStore } from "@/store/cartStore"
import { useUserStore } from "@/store/userStore"
import { useAuthModalStore } from "@/store/authModalStore"
import { productApi, searchApi_es, cartApi, commentApi, collectionApi } from "@/utils/api"
import { useEffect, useState, useMemo } from "react"
import {
  Minus, Plus, ShoppingCart, Heart, Share2, ChevronRight, Loader2,
  Star, ShieldCheck, Truck, RefreshCw, MessageSquare, ChevronDown, ChevronUp,
} from "lucide-react"
import { toast } from "sonner"

interface SpecGroup {
  name: string
  values: string[]
}

interface SelectedSku {
  productSkuId: number
  price: number
  stock: number
  lockStock: number
  realStock: number
  pic: string
}

export function ProductDetail() {
  const { id } = useParams()
  const setCartItems = useCartStore((s) => s.setItems)
  const isAuthenticated = useUserStore((s) => s.isAuthenticated)
  const { openAuth } = useAuthModalStore()
  const [product, setProduct] = useState<any>(null)
  const [relatedProducts, setRelatedProducts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [quantity, setQuantity] = useState(1)
  const [selectedImage, setSelectedImage] = useState("")

  // SKU 选择器状态
  const [selectedSpecs, setSelectedSpecs] = useState<Record<string, string>>({})
  const [showDetail, setShowDetail] = useState(false)

  // 收藏状态
  const [isCollected, setIsCollected] = useState(false)

  useEffect(() => {
    if (!id || !isAuthenticated) return
    collectionApi.getList(1, 100)
      .then((data: any) => {
        const list = data?.list || data?.records || []
        const found = list.some((item: any) => String(item.productId) === id)
        setIsCollected(found)
      })
      .catch(() => {})
  }, [id, isAuthenticated])

  const handleToggleCollection = async () => {
    if (!isAuthenticated) { toast.error("请先登录"); openAuth("login"); return }
    if (!id) return
    const numId = parseInt(id)
    try {
      if (isCollected) {
        await collectionApi.remove(numId)
        setIsCollected(false)
        toast.success("已取消收藏")
      } else {
        await collectionApi.add(numId)
        setIsCollected(true)
        toast.success("已收藏")
      }
    } catch {
      toast.error(isCollected ? "取消收藏失败" : "收藏失败")
    }
  }

  // 评论状态
  const [comments, setComments] = useState<any[]>([])
  const [commentPage, setCommentPage] = useState(1)
  const [commentTotal, setCommentTotal] = useState(0)
  const [commentLoading, setCommentLoading] = useState(false)
  const [commentTotalPages, setCommentTotalPages] = useState(0)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    const numId = parseInt(id)
    Promise.all([
      productApi.getDetail(numId),
      searchApi_es.recommend(numId, 0, 4).catch(() => []),
    ]).then(([detail, related]: any[]) => {
      setProduct(detail)
      setRelatedProducts(related?.list || related?.records || [])
      const img = detail?.product?.pic || detail?.pic || ""
      setSelectedImage(img)
    }).catch(() => {
      toast.error("加载商品详情失败")
    }).finally(() => setLoading(false))
  }, [id])

  // 加载评论
  useEffect(() => {
    if (!id || !product) return
    setCommentLoading(true)
    const numId = parseInt(id)
    Promise.all([
      commentApi.getList(numId, commentPage, 5),
      commentApi.getCount(numId),
    ]).then(([listData, count]: any[]) => {
      setComments(listData?.list || [])
      setCommentTotalPages(listData?.totalPage || 0)
      setCommentTotal(count ?? 0)
    }).catch(() => {})
      .finally(() => setCommentLoading(false))
  }, [id, product, commentPage])

  const p = product?.product || product || {}
  const brand = product?.brand || {}

  // ---- SKU 规格解析 ----
  const skuStockList = product?.skuStockList || []
  const specGroups = useMemo<SpecGroup[]>(() => {
    if (!skuStockList.length) return []
    const groupMap: Record<string, Set<string>> = {}
    skuStockList.forEach((sku: any) => {
      if (!sku.spData) return
      try {
        const attrs = JSON.parse(sku.spData)
        attrs.forEach((attr: { key: string; value: string }) => {
          if (!groupMap[attr.key]) groupMap[attr.key] = new Set()
          groupMap[attr.key].add(attr.value)
        })
      } catch { /* ignore parse errors */ }
    })
    return Object.entries(groupMap).map(([name, values]) => ({
      name,
      values: Array.from(values),
    }))
  }, [skuStockList])

  // 根据已选规格找出匹配的 SKU
  const matchedSku = useMemo<SelectedSku | null>(() => {
    const selectedKeys = Object.keys(selectedSpecs)
    if (selectedKeys.length === 0 || selectedKeys.length < specGroups.length) return null
    for (const sku of skuStockList) {
      if (!sku.spData) continue
      try {
        const attrs = JSON.parse(sku.spData)
        const match = attrs.every(
          (attr: { key: string; value: string }) =>
            selectedSpecs[attr.key] === attr.value
        )
        if (match) {
          const s = sku.stock || 0
          const ls = sku.lockStock || 0
          return {
            productSkuId: sku.id,
            price: parseFloat(sku.price || 0),
            stock: s,
            lockStock: ls,
            realStock: s - ls,
            pic: sku.pic || "",
          }
        }
      } catch { /* skip */ }
    }
    return null
  }, [selectedSpecs, specGroups, skuStockList])

  const handleSpecSelect = (groupName: string, value: string) => {
    setSelectedSpecs((prev) => {
      if (prev[groupName] === value) {
        const next = { ...prev }
        delete next[groupName]
        return next
      }
      return { ...prev, [groupName]: value }
    })
  }

  // ---- 商品数据 ----
  const images = p.albumPics
    ? p.albumPics.split(",").filter(Boolean)
    : [p.pic || selectedImage]
  const displayImage = matchedSku?.pic || selectedImage || p.pic || images[0] || ""
  const displayPrice = matchedSku ? matchedSku.price : parseFloat(p.price || 0)
  const originalPrice = parseFloat(p.originalPrice || 0)
  const displayStock = matchedSku !== null ? matchedSku.realStock : (p.stock || 0)
  const brandName = p.brandName || product?.brandName || ""
  const productName = p.name || product?.name || ""
  const subTitle = p.subTitle || product?.subTitle || ""
  const saleCount = p.sale || 0

  // 服务承诺（serviceIds: 1=无忧退货,2=快速退款,3=免费包邮）
  const serviceIds: number[] = p.serviceIds
    ? p.serviceIds.split(",").map(Number).filter(Boolean)
    : []
  const serviceLabels: Record<number, { label: string; icon: any }> = {
    1: { label: "无忧退货", icon: RefreshCw },
    2: { label: "快速退款", icon: ShieldCheck },
    3: { label: "免费包邮", icon: Truck },
  }

  // 属性/参数列表（type=1 的参数）
  const attributeList = product?.productAttributeList || []
  const attributeValueList = product?.productAttributeValueList || []
  const paramAttributes = attributeList.filter((a: any) => a.type === 1)

  // 优惠券
  const couponList = product?.couponList || []

  if (loading) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 flex justify-center">
        <Loader2 className="animate-spin text-[#e02020]" size={48} />
      </div>
    )
  }

  if (!product) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-20 text-center">
        <p className="text-gray-500 text-lg">商品不存在或已下架</p>
        <Link to="/" className="text-[#e02020] hover:underline mt-4 inline-block">返回首页</Link>
      </div>
    )
  }

  const handleAddToCart = async () => {
    if (!product) return
    const numId = parseInt(id!)

    if (!isAuthenticated) {
      toast.error("请先登录后再加入购物车")
      openAuth("login")
      return
    }

    if (specGroups.length > 0 && !matchedSku) {
      toast.error("请选择商品规格后再加入购物车")
      return
    }

    try {
      const addData: any = { productId: numId, quantity }
      if (matchedSku) addData.productSkuId = matchedSku.productSkuId
      await cartApi.add(addData)
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
        }))
      )
      toast.success("已加入购物车")
    } catch {
      toast.error("加入购物车失败")
    }
  }

  const renderStars = (star: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        size={14}
        className={i < star ? "fill-yellow-400 text-yellow-400" : "text-gray-200"}
      />
    ))
  }

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1 text-sm text-gray-500 mb-6">
        <Link to="/" className="hover:text-[#e02020]">首页</Link>
        <ChevronRight size={14} />
        <span className="text-gray-800">{productName}</span>
      </div>

      {/* ---- 商品主区域 ---- */}
      <div className="bg-white rounded-xl p-8 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {/* 左侧：商品图片 */}
          <div>
            <div className="aspect-square bg-gray-50 rounded-xl overflow-hidden mb-4">
              <img src={displayImage} alt={productName} className="w-full h-full object-cover" />
            </div>
            {images.length > 1 && (
              <div className="flex gap-2 flex-wrap">
                {images.map((img: string, i: number) => (
                  <button key={i} onClick={() => setSelectedImage(img)}
                    className={`w-16 h-16 rounded-lg border-2 overflow-hidden flex-shrink-0 ${img === displayImage ? "border-[#e02020]" : "border-gray-200"}`}>
                    <img src={img} alt="" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 右侧：商品信息 */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">{productName}</h1>
            {subTitle && <p className="text-gray-500 text-sm mb-4">{subTitle}</p>}

            {/* 销量 */}
            <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
              <span>销量 <strong className="text-gray-800">{saleCount}</strong></span>
              {originalPrice > 0 && (
                <span>市场价 <strong className="text-gray-400 line-through">¥{originalPrice.toFixed(2)}</strong></span>
              )}
            </div>

            {/* 价格 */}
            <div className="bg-red-50 rounded-lg p-4 mb-6">
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-bold text-[#e02020]">¥{displayPrice.toFixed(2)}</span>
                {originalPrice > displayPrice && (
                  <span className="text-lg text-gray-400 line-through">¥{originalPrice.toFixed(2)}</span>
                )}
                {originalPrice > displayPrice && (
                  <span className="bg-[#e02020] text-white text-xs px-2 py-0.5 rounded">
                    省¥{(originalPrice - displayPrice).toFixed(2)}
                  </span>
                )}
              </div>
            </div>

            {/* 品牌 */}
            {brandName && (
              <div className="mb-4 flex items-center gap-2 text-sm text-gray-600">
                <span>品牌：</span>
                <span className="font-medium text-gray-800">{brandName}</span>
              </div>
            )}

            {/* ---- SKU 规格选择 ---- */}
            {specGroups.map((group) => (
              <div key={group.name} className="mb-4">
                <div className="text-sm text-gray-600 mb-2">{group.name}</div>
                <div className="flex flex-wrap gap-2">
                  {group.values.map((val) => {
                    const selected = selectedSpecs[group.name] === val
                    return (
                      <button
                        key={val}
                        onClick={() => handleSpecSelect(group.name, val)}
                        className={`px-4 py-1.5 text-sm border rounded-lg transition-all ${
                          selected
                            ? "border-[#e02020] bg-red-50 text-[#e02020] font-medium"
                            : "border-gray-200 text-gray-700 hover:border-gray-400"
                        }`}
                      >
                        {val}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}

            {/* 库存 */}
            <div className="mb-4 text-sm text-gray-600">
              库存状态：
              <span className={displayStock > 0 ? "text-green-600 font-medium" : "text-red-500 font-medium"}>
                {displayStock > 0
                  ? `有货（可用${displayStock}件${matchedSku ? ` / 总量${matchedSku.stock}件` : ""}）`
                  : "缺货"}
              </span>
            </div>

            {/* 数量 */}
            <div className="flex items-center gap-4 mb-6">
              <span className="text-sm text-gray-600">数量：</span>
              <div className="flex items-center border rounded-lg">
                <button onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                  className="p-2 hover:bg-gray-100 transition-colors"><Minus size={16} /></button>
                <span className="w-12 text-center font-medium">{quantity}</span>
                <button onClick={() => setQuantity((q) => Math.min(displayStock || 999, q + 1))}
                  className="p-2 hover:bg-gray-100 transition-colors"><Plus size={16} /></button>
              </div>
            </div>

            {/* 服务承诺 */}
            {serviceIds.length > 0 && (
              <div className="mb-4 flex flex-wrap gap-4 text-xs text-gray-500">
                {serviceIds.map((sid) => {
                  const svc = serviceLabels[sid]
                  if (!svc) return null
                  const Icon = svc.icon
                  return (
                    <span key={sid} className="flex items-center gap-1">
                      <Icon size={14} className="text-green-600" /> {svc.label}
                    </span>
                  )
                })}
              </div>
            )}

            {/* 优惠券 */}
            {couponList.length > 0 && (
              <div className="mb-4 flex flex-wrap gap-2">
                {couponList.map((c: any) => (
                  <span key={c.id} className="text-xs bg-orange-50 text-orange-600 border border-orange-200 rounded px-2 py-0.5">
                    {c.name} {c.minPoint > 0 ? `满¥${c.minPoint}` : "无门槛"}减¥{c.amount}
                  </span>
                ))}
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex gap-4 mb-8">
              <button
                onClick={handleAddToCart}
                disabled={displayStock <= 0}
                className="flex-1 bg-[#e02020] text-white py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ShoppingCart size={20} /> {displayStock > 0 ? "加入购物车" : "暂时缺货"}
              </button>
              <button onClick={handleToggleCollection}
                className={`px-4 py-3 border rounded-lg transition-colors ${
                  isCollected
                    ? "bg-red-50 text-[#e02020] border-[#e02020]"
                    : "border-gray-200 hover:bg-red-50 hover:text-[#e02020] hover:border-[#e02020]"
                }`}>
                <Heart size={20} className={isCollected ? "fill-[#e02020] text-[#e02020]" : ""} />
              </button>
              <button className="px-4 py-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <Share2 size={20} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ---- 商品详情 + 评价 Tab ---- */}
      <div className="mt-10 bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="flex border-b">
          <button
            onClick={() => setShowDetail(false)}
            className={`px-6 py-3 text-sm font-medium transition-colors ${
              !showDetail ? "text-[#e02020] border-b-2 border-[#e02020]" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            商品详情
          </button>
          <button
            onClick={() => setShowDetail(true)}
            className={`px-6 py-3 text-sm font-medium transition-colors ${
              showDetail ? "text-[#e02020] border-b-2 border-[#e02020]" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            商品评价 ({commentTotal})
          </button>
        </div>

        <div className="p-6">
          {/* Tab: 商品详情 */}
          {!showDetail && (
            <div className="space-y-8">
              {/* 属性参数表 */}
              {paramAttributes.length > 0 && (
                <div>
                  <h3 className="text-base font-bold text-gray-900 mb-3">商品参数</h3>
                  <table className="w-full text-sm">
                    <tbody>
                      {paramAttributes.map((attr: any) => {
                        const attrVal = attributeValueList.find(
                          (v: any) => v.productAttributeId === attr.id
                        )
                        return (
                          <tr key={attr.id} className="border-b border-gray-50">
                            <td className="py-2.5 pr-4 text-gray-500 w-32 bg-gray-50/50 pl-3">{attr.name}</td>
                            <td className="py-2.5 pl-4 text-gray-800">{attrVal?.value || "-"}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {/* 商品描述 */}
              {p.detailHtml && (
                <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: p.detailHtml }} />
              )}
              {!p.detailHtml && p.description && (
                <div>
                  <h3 className="text-base font-bold text-gray-900 mb-3">商品描述</h3>
                  <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{p.description}</p>
                </div>
              )}
              {!p.detailHtml && !p.description && (
                <p className="text-sm text-gray-400 text-center py-8">暂无详细描述</p>
              )}
            </div>
          )}

          {/* Tab: 商品评价 */}
          {showDetail && (
            <div>
              {commentLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="animate-spin text-[#e02020]" size={32} />
                </div>
              ) : comments.length === 0 ? (
                <div className="text-center py-12">
                  <MessageSquare size={40} className="mx-auto text-gray-200 mb-3" />
                  <p className="text-gray-400 text-sm">暂无评价</p>
                </div>
              ) : (
                <div className="space-y-5">
                  {comments.map((c: any) => (
                    <div key={c.id} className="border-b border-gray-50 pb-5 last:border-0">
                      <div className="flex items-center gap-3 mb-2">
                        {c.memberIcon ? (
                          <img src={c.memberIcon} className="w-8 h-8 rounded-full object-cover" alt="" />
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs text-gray-500">
                            {c.memberNickName?.[0] || "?"}
                          </div>
                        )}
                        <span className="text-sm font-medium text-gray-800">
                          {c.memberNickName || "匿名用户"}
                        </span>
                        <div className="flex items-center">{renderStars(c.star || 5)}</div>
                        <span className="text-xs text-gray-400 ml-auto">
                          {c.createTime ? new Date(c.createTime).toLocaleDateString("zh-CN") : ""}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 leading-relaxed">{c.content}</p>
                      {c.pics && (
                        <div className="flex gap-2 mt-2">
                          {c.pics.split(",").filter(Boolean).map((pic: string, i: number) => (
                            <img key={i} src={pic} alt="" className="w-16 h-16 rounded-lg object-cover border" />
                          ))}
                        </div>
                      )}
                      {c.productAttribute && (
                        <p className="text-xs text-gray-400 mt-1">已购：{c.productAttribute}</p>
                      )}
                    </div>
                  ))}

                  {/* 评论分页 */}
                  {commentTotalPages > 1 && (
                    <div className="flex justify-center items-center gap-2 pt-4">
                      <button
                        disabled={commentPage <= 1}
                        onClick={() => setCommentPage((p) => Math.max(1, p - 1))}
                        className="px-3 py-1 text-sm border rounded-md hover:bg-gray-50 disabled:opacity-40"
                      >
                        上一页
                      </button>
                      <span className="text-sm text-gray-500">
                        {commentPage} / {commentTotalPages}
                      </span>
                      <button
                        disabled={commentPage >= commentTotalPages}
                        onClick={() => setCommentPage((p) => p + 1)}
                        className="px-3 py-1 text-sm border rounded-md hover:bg-gray-50 disabled:opacity-40"
                      >
                        下一页
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ---- 品牌信息 ---- */}
      {brand?.logo && (
        <div className="mt-10 bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-4">
            <img src={brand.logo} alt={brand.name} className="w-16 h-16 object-contain rounded-lg border p-1" />
            <div>
              <h3 className="font-bold text-gray-900">{brand.name}</h3>
              {brand.brandStory && (
                <p className="text-sm text-gray-500 mt-1 line-clamp-2">{brand.brandStory}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ---- 相关推荐 ---- */}
      {relatedProducts.length > 0 && (
        <div className="mt-10">
          <h2 className="text-xl font-bold mb-4">相关推荐</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {relatedProducts.map((item: any) => (
              <Link key={item.id} to={`/product/${item.id}`}
                className="bg-white rounded-lg p-4 hover:shadow-lg transition-shadow group">
                <div className="aspect-square bg-gray-50 rounded-lg overflow-hidden mb-3">
                  <img src={item.pic || item.image || ""}
                    alt={item.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                </div>
                <h3 className="text-sm text-gray-800 line-clamp-2 mb-2">{item.name}</h3>
                <div className="flex items-center gap-1 text-[#e02020] font-bold">
                  ¥{parseFloat(item.price || 0).toFixed(2)}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
