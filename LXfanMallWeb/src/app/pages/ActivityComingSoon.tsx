import { Link } from "react-router"
import { CalendarX } from "lucide-react"

export function ActivityComingSoon() {
  return (
    <div className="max-w-[1440px] mx-auto px-6 py-20 text-center">
      <div className="bg-white rounded-xl p-16 shadow-sm max-w-md mx-auto">
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <CalendarX size={40} className="text-gray-300" />
        </div>
        <h2 className="text-xl font-bold text-gray-800 mb-3">当前活动暂未开放</h2>
        <p className="text-gray-500 text-sm mb-8">敬请期待，更多精彩活动即将上线</p>
        <Link
          to="/"
          className="inline-block bg-[#e02020] text-white px-8 py-3 rounded-lg hover:bg-[#c01010] transition-colors font-medium"
        >
          返回首页
        </Link>
      </div>
    </div>
  )
}
