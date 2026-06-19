import type { HomeSummaryResult, HomeChartResult, HomeProductOverview, HomeMemberOverview } from '@/types/home'
import http from '@/utils/http'

/**
 * 获取首页汇总统计
 */
export function getHomeSummaryAPI() {
  return http<HomeSummaryResult>({
    url: '/home/summary',
    method: 'get',
  })
}

/**
 * 获取订单统计折线图数据
 */
export function getHomeChartAPI(params: { startDate: string; endDate: string }) {
  return http<HomeChartResult[]>({
    url: '/home/chart',
    method: 'get',
    params,
  })
}

/**
 * 获取商品总览
 */
export function getProductOverviewAPI() {
  return http<HomeProductOverview>({
    url: '/home/productOverview',
    method: 'get',
  })
}

/**
 * 获取用户总览
 */
export function getMemberOverviewAPI() {
  return http<HomeMemberOverview>({
    url: '/home/memberOverview',
    method: 'get',
  })
}
