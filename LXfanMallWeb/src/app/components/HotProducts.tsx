import { useState } from "react"
import { Link } from "react-router"
import { ShoppingCart, TrendingUp } from "lucide-react"
import { ImageWithFallback } from "./figma/ImageWithFallback"

interface HotProduct {
  id: number
  name: string
  pic?: string
  price?: number
  originalPrice?: number
  subTitle?: string
  sale?: number
}

interface HotProductsProps {
  products?: HotProduct[]
}

export function HotProducts({ products }: HotProductsProps) {
  const [hoveredId, setHoveredId] = useState<number | null>(null)

  const list = Array.isArray(products) ? products : []

  if (list.length === 0) {
    return (
      <div className="bg-white max-w-[1440px] mx-auto my-3 shadow-sm rounded-sm overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <TrendingUp size={22} className="text-[#e02020]" />
            <h2 className="text-xl font-black text-gray-800">热门商品推荐</h2>
          </div>
        </div>
        <div className="p-12 text-center text-gray-400 text-sm">暂无推荐商品</div>
      </div>
    )
  }

  return (
    <div className="bg-white max-w-[1440px] mx-auto my-3 shadow-sm rounded-sm overflow-hidden">
      {/* Section header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <TrendingUp size={22} className="text-[#e02020]" />
          <h2 className="text-xl font-black text-gray-800">热门商品推荐</h2>
          <span className="bg-red-50 text-[#e02020] text-xs px-2 py-0.5 rounded-full border border-red-200">
            热销推荐
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/category/all" className="flex items-center gap-1 text-sm text-[#e02020] hover:text-[#c01010] transition-colors">
            查看更多 →
          </Link>
        </div>
      </div>

      {/* Products grid - 两行四列布局 */}
      <div className="grid grid-cols-4 gap-0 divide-x divide-y divide-gray-100">
        {list.map((product) => (
          <Link
            key={product.id}
            to={`/product/${product.id}`}
            className="relative p-5 cursor-pointer group overflow-hidden block"
            onMouseEnter={() => setHoveredId(product.id)}
            onMouseLeave={() => setHoveredId(null)}
          >
            {/* Hover background */}
            <div
              className={`absolute inset-0 bg-red-50/50 transition-opacity duration-200 ${
                hoveredId === product.id ? "opacity-100" : "opacity-0"
              }`}
            />

            <div className="relative">
              {/* Product image */}
              <div className="overflow-hidden rounded-sm mb-3 pt-4">
                <ImageWithFallback
                  src={product.pic || ""}
                  alt={product.name}
                  className={`w-full h-44 object-cover transition-transform duration-300 ${
                    hoveredId === product.id ? "scale-110" : "scale-100"
                  }`}
                />
              </div>

              {/* Product info */}
              <div className="text-sm text-gray-700 mb-1 line-clamp-2 h-10 leading-5">
                {product.name}
              </div>

              {/* Subtitle */}
              {product.subTitle && (
                <p className="text-xs text-gray-400 mb-1.5 line-clamp-1">{product.subTitle}</p>
              )}

              {/* Sales count */}
              {product.sale !== undefined && product.sale > 0 && (
                <div className="flex items-center gap-1.5 mb-1.5">
                  <span className="text-xs text-gray-400">已售 {product.sale} 件</span>
                </div>
              )}

              {/* Price */}
              <div className="flex items-baseline gap-2 mb-3">
                <span className="text-[#e02020] font-black">¥{(product.price || 0).toFixed(2)}</span>
                {product.originalPrice && product.originalPrice > product.price! && (
                  <>
                    <span className="text-gray-400 text-xs line-through">
                      ¥{product.originalPrice.toFixed(2)}
                    </span>
                    <span className="text-[#e02020] text-xs bg-red-50 px-1 border border-red-200 rounded">
                      省¥{(product.originalPrice - (product.price || 0)).toFixed(2)}
                    </span>
                  </>
                )}
              </div>

              {/* Add to cart button — 跳转到商品详情选择规格 */}
              <Link
                to={`/product/${product.id}`}
                onClick={(e) => e.stopPropagation()}
                className={`block w-full py-2 text-sm font-medium rounded-sm flex items-center justify-center gap-2 transition-all duration-200 ${
                  hoveredId === product.id
                    ? "bg-[#e02020] text-white shadow-md"
                    : "bg-white border border-gray-200 text-gray-600 hover:border-[#e02020] hover:text-[#e02020]"
                }`}
              >
                <ShoppingCart size={14} />
                选择规格
              </Link>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
