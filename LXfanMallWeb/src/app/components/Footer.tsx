import { Shield, Truck, RefreshCw, Headphones, Award } from "lucide-react";

const SERVICE_ITEMS = [
  { icon: Shield, label: "正品保障", desc: "假一赔十承诺" },
  { icon: Truck, label: "极速配送", desc: "当日达/次日达" },
  { icon: RefreshCw, label: "无忧退换", desc: "7天无理由退货" },
  { icon: Headphones, label: "专属客服", desc: "24小时在线" },
  { icon: Award, label: "品质甄选", desc: "严选优质商品" },
];

const FOOTER_LINKS = [
  {
    title: "关于我们",
    links: ["公司简介", "联系我们", "加入我们", "媒体报道", "投资者关系"],
  },
  {
    title: "帮助中心",
    links: ["新手指南", "购物流程", "会员介绍", "积分规则", "常见问题"],
  },
  {
    title: "售后服务",
    links: ["退换货政策", "投诉建议", "质量问题", "物流追踪", "价保服务"],
  },
  {
    title: "合作伙伴",
    links: ["招商合作", "品牌入驻", "联盟推广", "广告合作", "企业采购"],
  },
  {
    title: "社交媒体",
    links: ["官方微博", "微信公众号", "抖音账号", "小红书", "B站"],
  },
];

export function Footer() {
  return (
    <footer className="bg-white mt-3">
      {/* Service guarantee strip */}
      <div className="bg-gray-50 border-t border-b border-gray-200">
        <div className="max-w-[1440px] mx-auto px-6 py-5">
          <div className="grid grid-cols-5 gap-4">
            {SERVICE_ITEMS.map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-3 group cursor-pointer"
              >
                <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center shrink-0 group-hover:bg-[#e02020] transition-colors">
                  <item.icon
                    size={18}
                    className="text-[#e02020] group-hover:text-white transition-colors"
                  />
                </div>
                <div>
                  <div className="text-sm font-semibold text-gray-800 group-hover:text-[#e02020] transition-colors">
                    {item.label}
                  </div>
                  <div className="text-xs text-gray-500">{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main footer content */}
      <div className="max-w-[1440px] mx-auto px-6 py-10">
        <div className="grid grid-cols-6 gap-8">
          {/* Brand */}
          <div className="col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 bg-[#e02020] rounded-full flex items-center justify-center">
                <span className="text-white font-black text-sm">LX</span>
              </div>
              <div>
                <div className="font-black text-lg text-gray-800">LXfanMall</div>
                <div className="text-xs text-gray-400">智能购物平台</div>
              </div>
            </div>
            <p className="text-xs text-gray-500 leading-5 mb-4">
              LXfanMall 是一家以技术驱动的智能电商平台，致力于为用户提供最优质的购物体验。
            </p>
            <div className="flex gap-2">
              {["微", "抖", "红", "B"].map((icon, i) => (
                <div
                  key={i}
                  className="w-8 h-8 bg-gray-100 hover:bg-[#e02020] rounded-full flex items-center justify-center text-xs font-bold text-gray-500 hover:text-white cursor-pointer transition-all duration-200"
                >
                  {icon}
                </div>
              ))}
            </div>
          </div>

          {/* Footer links */}
          {FOOTER_LINKS.map((section) => (
            <div key={section.title}>
              <h4 className="text-sm font-semibold text-gray-800 mb-3 pb-2 border-b border-gray-100">
                {section.title}
              </h4>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-xs text-gray-500 hover:text-[#e02020] transition-colors"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* App download & payment methods */}
        <div className="mt-8 pt-6 border-t border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="text-xs text-gray-400">支付方式：</div>
            {["微信支付", "支付宝", "银联", "Apple Pay", "花呗分期"].map((pay) => (
              <span
                key={pay}
                className="text-xs bg-gray-50 border border-gray-200 px-2.5 py-1 rounded text-gray-500 hover:border-[#e02020] hover:text-[#e02020] cursor-pointer transition-colors"
              >
                {pay}
              </span>
            ))}
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span>官方 App 下载</span>
            <div className="flex gap-2">
              {["iOS", "Android"].map((p) => (
                <span
                  key={p}
                  className="bg-gray-800 text-white px-3 py-1.5 rounded-sm hover:bg-[#e02020] cursor-pointer transition-colors"
                >
                  {p}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Copyright bar */}
      <div className="bg-gray-800 text-white">
        <div className="max-w-[1440px] mx-auto px-6 py-4 flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center gap-4">
            <span>© 2024 LXfanMall. 保留所有权利.</span>
            <span className="text-gray-600">|</span>
            <a href="#" className="hover:text-white transition-colors">隐私政策</a>
            <a href="#" className="hover:text-white transition-colors">用户协议</a>
            <a href="#" className="hover:text-white transition-colors">Cookie设置</a>
          </div>
          <div className="flex items-center gap-4">
            <span>增值电信业务经营许可证：B2-20230001</span>
            <span className="text-gray-600">|</span>
            <span>京ICP备2024001号</span>
            <span className="text-gray-600">|</span>
            <span>营业执照</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
