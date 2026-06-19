import type {
  TokenUsageSummaryResult,
  TokenUsageChartResult,
  TokenUsageRankingResult,
  TokenUsageIntentResult,
  TokenUsageDetailResult,
} from '@/types/tokenUsage'
import type { CommonPage } from '@/types/common'
import http from '@/utils/http'

/** 获取Token用量汇总统计 */
export function getTokenUsageSummaryAPI() {
  return http<TokenUsageSummaryResult>({
    url: '/home/tokenUsage/summary',
    method: 'get',
  })
}

/** 获取Token用量折线图数据 */
export function getTokenUsageChartAPI(params: { startDate: string; endDate: string }) {
  return http<TokenUsageChartResult[]>({
    url: '/home/tokenUsage/chart',
    method: 'get',
    params,
  })
}

/** 获取用户Token用量排行 */
export function getTokenUsageRankingAPI(limit: number = 10) {
  return http<TokenUsageRankingResult[]>({
    url: '/home/tokenUsage/ranking',
    method: 'get',
    params: { limit },
  })
}

/** 获取意图分布 */
export function getTokenUsageIntentDistributionAPI() {
  return http<TokenUsageIntentResult[]>({
    url: '/home/tokenUsage/intentDistribution',
    method: 'get',
  })
}

/** 分页查询Token用量明细 */
export function getTokenUsageListAPI(params: {
  username?: string
  intent?: string
  startDate?: string
  endDate?: string
  pageNum: number
  pageSize: number
}) {
  return http<CommonPage<TokenUsageDetailResult>>({
    url: '/home/tokenUsage/list',
    method: 'get',
    params,
  })
}
