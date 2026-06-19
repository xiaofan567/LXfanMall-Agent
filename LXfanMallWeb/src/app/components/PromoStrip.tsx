import { Tag, Gift, CreditCard, Percent } from "lucide-react";

const PROMOS = [
  { icon: Tag, label: "新人专享", desc: "注册领50元大礼包", color: "text-red-500", bg: "bg-red-50" },
  { icon: Gift, label: "每日签到", desc: "签到赚积分换好礼", color: "text-orange-500", bg: "bg-orange-50" },
  { icon: CreditCard, label: "分期免息", desc: "花呗/白条分12期", color: "text-blue-500", bg: "bg-blue-50" },
  { icon: Percent, label: "超值折扣", desc: "每日10点准时开抢", color: "text-purple-500", bg: "bg-purple-50" },
];

export function PromoStrip() {
  return (
    <div className="max-w-[1440px] mx-auto px-6 mt-3">
      <div className="grid grid-cols-4 gap-3">
        {PROMOS.map((promo) => (
          <div
            key={promo.label}
            className={`${promo.bg} rounded-sm p-3 flex items-center gap-3 cursor-pointer hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 border border-transparent hover:border-current`}
            style={{ borderColor: "transparent" }}
          >
            <div className={`w-10 h-10 rounded-full bg-white flex items-center justify-center shrink-0 shadow-sm`}>
              <promo.icon size={18} className={promo.color} />
            </div>
            <div>
              <div className={`text-sm font-semibold ${promo.color}`}>{promo.label}</div>
              <div className="text-xs text-gray-500">{promo.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
