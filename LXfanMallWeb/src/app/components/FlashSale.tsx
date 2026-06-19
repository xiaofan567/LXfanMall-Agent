import { useState, useEffect } from "react";
import { Zap, ChevronRight } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

const FLASH_PRODUCTS = [
  {
    id: 1,
    name: "Apple iPhone 15 Pro",
    image: "https://images.unsplash.com/photo-1502096472573-eaac515392c6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400",
    price: 7299,
    originalPrice: 9999,
    sold: 89,
    stock: 100,
  },
  {
    id: 2,
    name: "Sony 无线降噪耳机",
    image: "https://images.unsplash.com/photo-1640300065113-738f2abb8ba6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400",
    price: 899,
    originalPrice: 1499,
    sold: 73,
    stock: 100,
  },
  {
    id: 3,
    name: "Nike Air Max 运动鞋",
    image: "https://images.unsplash.com/photo-1770177132209-e67de0b6dad8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400",
    price: 499,
    originalPrice: 899,
    sold: 92,
    stock: 100,
  },
  {
    id: 4,
    name: "联想笔记本电脑",
    image: "https://images.unsplash.com/photo-1650387248585-7c0c9ac6688b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400",
    price: 3999,
    originalPrice: 5499,
    sold: 56,
    stock: 100,
  },
  {
    id: 5,
    name: "精华面霜套装",
    image: "https://images.unsplash.com/photo-1600417098578-1e858e93dc88?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400",
    price: 199,
    originalPrice: 459,
    sold: 88,
    stock: 100,
  },
  {
    id: 6,
    name: "高端机械键盘",
    image: "https://images.unsplash.com/photo-1502096472573-eaac515392c6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400",
    price: 329,
    originalPrice: 599,
    sold: 65,
    stock: 100,
  },
];

function useCountdown(targetSeconds: number) {
  const [seconds, setSeconds] = useState(targetSeconds);

  useEffect(() => {
    const t = setInterval(() => setSeconds((s) => (s > 0 ? s - 1 : 0)), 1000);
    return () => clearInterval(t);
  }, []);

  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return { h, m, s };
}

export function FlashSale() {
  const { h, m, s } = useCountdown(2 * 3600 + 34 * 60 + 18);
  const [hoveredId, setHoveredId] = useState<number | null>(null);

  const pad = (n: number) => String(n).padStart(2, "0");

  return (
    <div className="bg-white my-3 shadow-sm rounded-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#e02020] to-[#ff4444] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Zap size={22} className="text-yellow-300 fill-yellow-300" />
          <span className="text-white text-xl font-black tracking-wide">限时秒杀</span>
          <div className="flex items-center gap-1 ml-2">
            <span className="text-yellow-300 text-xs">距结束</span>
            {[pad(h), pad(m), pad(s)].map((unit, i) => (
              <span key={i} className="flex items-center">
                <span className="bg-black/40 text-white text-sm font-mono font-bold px-1.5 py-0.5 rounded min-w-[26px] text-center">
                  {unit}
                </span>
                {i < 2 && <span className="text-yellow-300 font-bold mx-0.5">:</span>}
              </span>
            ))}
          </div>
        </div>
        <button className="flex items-center gap-1 text-white/90 hover:text-yellow-300 text-sm transition-colors">
          查看全部 <ChevronRight size={14} />
        </button>
      </div>

      {/* Products */}
      <div className="grid grid-cols-6 divide-x divide-gray-100">
        {FLASH_PRODUCTS.map((product) => (
          <div
            key={product.id}
            className={`p-4 cursor-pointer transition-all duration-200 ${
              hoveredId === product.id ? "bg-red-50 shadow-inner" : "hover:bg-red-50/50"
            }`}
            onMouseEnter={() => setHoveredId(product.id)}
            onMouseLeave={() => setHoveredId(null)}
          >
            <div className="relative overflow-hidden rounded-sm mb-2">
              <ImageWithFallback
                src={product.image}
                alt={product.name}
                className={`w-full h-36 object-cover transition-transform duration-300 ${
                  hoveredId === product.id ? "scale-110" : "scale-100"
                }`}
              />
              <div className="absolute top-1 left-1 bg-[#e02020] text-white text-xs px-1.5 py-0.5 rounded">
                {Math.round((1 - product.price / product.originalPrice) * 100)}%OFF
              </div>
            </div>
            <div className="text-xs text-gray-600 mb-1 truncate">{product.name}</div>
            <div className="flex items-baseline gap-1.5 mb-2">
              <span className="text-[#e02020] font-black">¥{product.price}</span>
              <span className="text-gray-400 text-xs line-through">¥{product.originalPrice}</span>
            </div>
            {/* Progress bar */}
            <div className="relative h-4 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#e02020] to-[#ff6644] rounded-full transition-all duration-1000"
                style={{ width: `${product.sold}%` }}
              />
              <span className="absolute inset-0 flex items-center justify-center text-[10px] text-white font-medium drop-shadow">
                已抢 {product.sold}%
              </span>
            </div>
            <button
              className={`w-full mt-2 py-1.5 text-xs font-medium rounded-sm transition-all duration-200 ${
                hoveredId === product.id
                  ? "bg-[#e02020] text-white scale-105 shadow-md"
                  : "bg-red-50 text-[#e02020] border border-red-200"
              }`}
            >
              立即抢购
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}