import { useEffect, useState } from "react"
import { BannerCarousel } from "../components/BannerCarousel"
import { PromoStrip } from "../components/PromoStrip"
import { HotProducts } from "../components/HotProducts"
import { MultiCategory } from "../components/MultiCategory"
import { homeApi } from "@/utils/api"

interface HomeData {
  advertiseList: any[]
  brandList: any[]
  homeFlashPromotion: any
  newProductList: any[]
  hotProductList: any[]
  subjectList: any[]
}

export function Home() {
  const [homeData, setHomeData] = useState<HomeData | null>(null)

  useEffect(() => {
    homeApi.getContent().then(setHomeData).catch(() => {
      // 后端不可用时使用组件内硬编码数据兜底
    })
  }, [])

  return (
    <main>
      {/* Banner + category */}
      <BannerCarousel ads={homeData?.advertiseList} />

      {/* Promo strip */}
      <PromoStrip />

      {/* Hot products */}
      <div className="max-w-[1440px] mx-auto px-6">
        <HotProducts products={homeData?.hotProductList} />
      </div>

      {/* Multi-category section */}
      <div className="max-w-[1440px] mx-auto px-6">
        <MultiCategory />
      </div>

      <div className="h-8" />
    </main>
  )
}
