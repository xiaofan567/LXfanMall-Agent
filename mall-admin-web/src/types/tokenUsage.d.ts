/** Token用量汇总统计 */
export type TokenUsageSummaryResult = {
  /** 今日Token总消耗 */
  todayTotalTokens: number
  /** 今日请求次数 */
  todayRequestCount: number
  /** 今日平均每次请求Token数 */
  todayAvgTokens: number
  /** 本周Token总消耗 */
  weeklyTotalTokens: number
  /** 本周请求次数 */
  weeklyRequestCount: number
  /** 本月Token总消耗 */
  monthlyTotalTokens: number
  /** 本月请求次数 */
  monthlyRequestCount: number
  /** 本月活跃用户数 */
  monthlyActiveUsers: number
  /** 总Token消耗 */
  totalTokens: number
  /** 总请求次数 */
  totalRequestCount: number
  /** 总用户数 */
  totalUsers: number
}

/** Token用量折线图数据项 */
export type TokenUsageChartResult = {
  /** 日期 (yyyy-MM-dd) */
  date: string
  /** Token消耗总量 */
  totalTokens: number
  /** 请求次数 */
  requestCount: number
}

/** Token用量用户排行 */
export type TokenUsageRankingResult = {
  /** 用户名 */
  username: string
  /** Token总消耗 */
  totalTokens: number
  /** 请求次数 */
  requestCount: number
}

/** Token用量意图分布 */
export type TokenUsageIntentResult = {
  /** 意图类型 */
  intent: string
  /** Token消耗总量 */
  totalTokens: number
  /** 请求次数 */
  requestCount: number
}

/** Token用量明细记录 */
export type TokenUsageDetailResult = {
  /** 记录ID */
  id: number
  /** 用户名 */
  username: string
  /** 会话ID */
  sessionId: string
  /** 意图分类 */
  intent: string
  /** 模型名称 */
  model: string
  /** 输入Token数 */
  promptTokens: number
  /** 输出Token数 */
  completionTokens: number
  /** 总Token数 */
  totalTokens: number
  /** 工具调用次数 */
  toolCalls: number
  /** 请求耗时(毫秒) */
  latencyMs: number
  /** 创建时间 */
  createTime: string
}
