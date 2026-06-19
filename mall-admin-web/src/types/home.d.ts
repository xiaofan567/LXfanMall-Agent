/** 首页汇总统计结果 */
export type HomeSummaryResult = {
  /** 今日订单总数 */
  todayOrderCount: number
  /** 今日销售总额 */
  todaySales: number
  /** 昨日销售总额 */
  yesterdaySales: number

  /** 待付款订单数 */
  pendingPaymentCount: number
  /** 已完成订单数 */
  completedOrderCount: number
  /** 待确认收货订单数 */
  deliveredOrderCount: number
  /** 待发货订单数 */
  pendingShipmentCount: number
  /** 已发货订单数 */
  shippedOrderCount: number
  /** 待处理退款申请数 */
  pendingRefundCount: number
  /** 待处理退货订单数 */
  pendingReturnCount: number
  /** 广告位即将到期数 */
  adExpiringCount: number

  /** 本月订单总数 */
  monthlyOrderCount: number
  /** 本周订单总数 */
  weeklyOrderCount: number
  /** 本月销售总额 */
  monthlySales: number
  /** 本周销售总额 */
  weeklySales: number
  /** 本月订单同比百分比 */
  monthlyOrderGrowth: string
  /** 本周订单同比百分比 */
  weeklyOrderGrowth: string
  /** 本月销售同比百分比 */
  monthlySalesGrowth: string
  /** 本周销售同比百分比 */
  weeklySalesGrowth: string
}

/** 首页折线图数据项 */
export type HomeChartResult = {
  /** 日期 (yyyy-MM-dd) */
  date: string
  /** 订单数量 */
  orderCount: number
  /** 订单金额 */
  orderAmount: number
}

/** 首页商品总览 */
export type HomeProductOverview = {
  /** 已下架商品数 */
  delistedCount: number
  /** 已上架商品数 */
  listedCount: number
  /** 库存紧张商品数 */
  lowStockCount: number
  /** 全部商品数 */
  totalCount: number
}

/** 首页用户总览 */
export type HomeMemberOverview = {
  /** 今日新增会员数 */
  todayNewCount: number
  /** 昨日新增会员数 */
  yesterdayNewCount: number
  /** 本月新增会员数 */
  monthNewCount: number
  /** 会员总数 */
  totalCount: number
}
