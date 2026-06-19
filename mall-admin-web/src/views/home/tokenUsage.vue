<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { dayjs } from 'element-plus'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import VChart from 'vue-echarts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'
import {
  getTokenUsageSummaryAPI,
  getTokenUsageChartAPI,
  getTokenUsageRankingAPI,
  getTokenUsageIntentDistributionAPI,
  getTokenUsageListAPI,
} from '@/apis/tokenUsage'
import type {
  TokenUsageSummaryResult,
  TokenUsageChartResult,
  TokenUsageRankingResult,
  TokenUsageIntentResult,
  TokenUsageDetailResult,
} from '@/types/tokenUsage'
import type { CommonPage } from '@/types/common'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

// ── 汇总数据 ──
const summaryData = ref<TokenUsageSummaryResult | null>(null)
const summaryLoading = ref(true)

// ── 折线图 ──
const lineChartData = ref<TokenUsageChartResult[]>([])
const chartLoading = ref(false)
const datePickerRange = ref<Date[]>([])

// ── 用户排行 ──
const rankingData = ref<TokenUsageRankingResult[]>([])

// ── 意图分布 ──
const intentData = ref<TokenUsageIntentResult[]>([])

// ── 明细表格 ──
const tableData = ref<TokenUsageDetailResult[]>([])
const tableTotal = ref(0)
const tableLoading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const filterUsername = ref('')
const filterIntent = ref('')

// 意图类型中文映射
const intentLabelMap: Record<string, string> = {
  product_recommend: '商品推荐',
  order_query: '订单查询',
  address_manage: '地址管理',
  cart_query: '购物车',
  chitchat: '闲聊',
  customer_service: '客服',
  knowledge_query: '知识库',
  unknown: '未知',
}

const getIntentLabel = (intent: string) => intentLabelMap[intent] || intent

// ── 初始化日期选择器为最近一周 ──
const initDatePickerRange = () => {
  const end = new Date()
  const start = new Date(end.getTime() - 1000 * 60 * 60 * 24 * 7)
  datePickerRange.value = [start, end] as Date[]
}

// ── 日期选择器快捷选项 ──
const shortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 1000 * 60 * 60 * 24 * 7)
      return [start, end]
    },
  },
  {
    text: '最近一月',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 1000 * 60 * 60 * 24 * 30)
      return [start, end]
    },
  },
]

// ── 数据加载 ──
const fetchSummary = async () => {
  try {
    const res = await getTokenUsageSummaryAPI()
    summaryData.value = res.data
  } catch (e) {
    console.error('获取Token汇总统计失败', e)
  }
}

const fetchChartData = async () => {
  chartLoading.value = true
  try {
    const startDate = dayjs(datePickerRange.value[0]).format('YYYY-MM-DD')
    const endDate = dayjs(datePickerRange.value[1]).format('YYYY-MM-DD')
    const res = await getTokenUsageChartAPI({ startDate, endDate })
    lineChartData.value = res.data ?? []
  } catch (e) {
    console.error('获取Token折线图数据失败', e)
    lineChartData.value = []
  } finally {
    chartLoading.value = false
  }
}

const fetchRanking = async () => {
  try {
    const res = await getTokenUsageRankingAPI(10)
    rankingData.value = res.data ?? []
  } catch (e) {
    console.error('获取用户排行失败', e)
  }
}

const fetchIntentDistribution = async () => {
  try {
    const res = await getTokenUsageIntentDistributionAPI()
    intentData.value = res.data ?? []
  } catch (e) {
    console.error('获取意图分布失败', e)
  }
}

const fetchList = async () => {
  tableLoading.value = true
  try {
    const params: Record<string, any> = {
      pageNum: pageNum.value,
      pageSize: pageSize.value,
    }
    if (filterUsername.value) params.username = filterUsername.value
    if (filterIntent.value) params.intent = filterIntent.value
    const res = await getTokenUsageListAPI(params as any)
    const page: CommonPage<TokenUsageDetailResult> = res.data
    tableData.value = page.list ?? []
    tableTotal.value = page.total ?? 0
  } catch (e) {
    console.error('获取Token明细列表失败', e)
  } finally {
    tableLoading.value = false
  }
}

const handleDatePickerChange = () => {
  fetchChartData()
}

const handleTablePageChange = (page: number) => {
  pageNum.value = page
  fetchList()
}

const handleTableSizeChange = (size: number) => {
  pageSize.value = size
  pageNum.value = 1
  fetchList()
}

const handleFilter = () => {
  pageNum.value = 1
  fetchList()
}

// ── 格式化 ──
const formatTokens = (val: number | undefined) => {
  if (val == null) return '0'
  if (val >= 1000000) return (val / 1000000).toFixed(1) + 'M'
  if (val >= 1000) return (val / 1000).toFixed(1) + 'K'
  return val.toString()
}

// ── ECharts 折线图配置 ──
const chartOption = computed(() => {
  const dates = lineChartData.value.map(item => item.date)
  const tokens = lineChartData.value.map(item => item.totalTokens)
  const counts = lineChartData.value.map(item => item.requestCount)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    legend: { data: ['Token消耗', '请求次数'] },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLabel: { formatter: '{value}', rotate: 0 },
    },
    yAxis: [
      { type: 'value', name: 'Token消耗', position: 'left', axisLabel: { formatter: '{value}' } },
      { type: 'value', name: '请求次数', position: 'right', axisLabel: { formatter: '{value}' } },
    ],
    series: [
      {
        name: 'Token消耗',
        type: 'line',
        areaStyle: {},
        data: tokens,
        smooth: true,
        itemStyle: { color: '#409EFF' },
      },
      {
        name: '请求次数',
        type: 'line',
        yAxisIndex: 1,
        areaStyle: {},
        data: counts,
        smooth: true,
        itemStyle: { color: '#67C23A' },
      },
    ],
  }
})

// ── ECharts 饼图配置 ──
const pieOption = computed(() => {
  const data = intentData.value.map(item => ({
    name: getIntentLabel(item.intent),
    value: item.totalTokens,
  }))
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        name: '意图分布',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{d}%' },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        data,
      },
    ],
  }
})

// ── 初始化 ──
onMounted(async () => {
  initDatePickerRange()
  await Promise.all([
    fetchSummary(),
    fetchChartData(),
    fetchRanking(),
    fetchIntentDistribution(),
    fetchList(),
  ])
  summaryLoading.value = false
})
</script>

<template>
  <div class="app-container" v-loading="summaryLoading">
    <!-- 汇总卡片 -->
    <el-row :gutter="20" class="summary-row">
      <el-col :span="6">
        <div class="summary-card">
          <div class="summary-label">今日Token消耗</div>
          <div class="summary-value color-primary">{{ formatTokens(summaryData?.todayTotalTokens) }}</div>
          <div class="summary-sub">今日请求 {{ summaryData?.todayRequestCount ?? 0 }} 次</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="summary-card">
          <div class="summary-label">本周Token消耗</div>
          <div class="summary-value color-success">{{ formatTokens(summaryData?.weeklyTotalTokens) }}</div>
          <div class="summary-sub">本周请求 {{ summaryData?.weeklyRequestCount ?? 0 }} 次</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="summary-card">
          <div class="summary-label">本月Token消耗</div>
          <div class="summary-value color-warning">{{ formatTokens(summaryData?.monthlyTotalTokens) }}</div>
          <div class="summary-sub">活跃用户 {{ summaryData?.monthlyActiveUsers ?? 0 }} 人</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="summary-card">
          <div class="summary-label">今日平均每次请求</div>
          <div class="summary-value color-danger">{{ formatTokens(summaryData?.todayAvgTokens) }}</div>
          <div class="summary-sub">总计 {{ formatTokens(summaryData?.totalTokens) }} tokens</div>
        </div>
      </el-col>
    </el-row>

    <!-- 折线图 + 意图分布 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <div class="out-border">
          <div class="layout-title">Token用量趋势</div>
          <div style="padding: 10px">
            <el-date-picker
              style="float: right; z-index: 1"
              size="small"
              v-model="datePickerRange"
              type="daterange"
              align="right"
              unlink-panels
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="shortcuts"
              @change="handleDatePickerChange"
            />
            <div style="height: 350px">
              <v-chart v-if="!chartLoading && lineChartData.length > 0" :option="chartOption" autoresize />
              <el-empty v-else-if="!chartLoading" description="暂无数据" :image-size="80" />
              <div v-else style="display: flex; justify-content: center; align-items: center; height: 100%">
                <el-skeleton :rows="5" animated />
              </div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="out-border">
          <div class="layout-title">意图分布</div>
          <div style="padding: 10px; height: 350px">
            <v-chart v-if="intentData.length > 0" :option="pieOption" autoresize />
            <el-empty v-else description="暂无数据" :image-size="80" />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 用户排行 -->
    <el-row :gutter="20" class="ranking-row">
      <el-col :span="24">
        <div class="out-border">
          <div class="layout-title">用户Token用量排行 Top 10</div>
          <div style="padding: 20px">
            <el-table :data="rankingData" stripe style="width: 100%">
              <el-table-column label="排名" width="80" align="center">
                <template #default="{ $index }">
                  <el-tag :type="$index < 3 ? 'danger' : 'info'" size="small">{{ $index + 1 }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="username" label="用户名" min-width="200" />
              <el-table-column prop="totalTokens" label="Token总消耗" min-width="200">
                <template #default="{ row }">
                  <span class="color-danger">{{ formatTokens(row.totalTokens) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="requestCount" label="请求次数" min-width="150" />
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 明细表格 -->
    <el-row :gutter="20" class="detail-row">
      <el-col :span="24">
        <div class="out-border">
          <div class="layout-title">Token用量明细</div>
          <div style="padding: 20px">
            <!-- 筛选条件 -->
            <el-form :inline="true" style="margin-bottom: 15px">
              <el-form-item label="用户名">
                <el-input v-model="filterUsername" placeholder="请输入用户名" clearable size="small" @keyup.enter="handleFilter" />
              </el-form-item>
              <el-form-item label="意图类型">
                <el-select v-model="filterIntent" placeholder="全部" clearable size="small">
                  <el-option v-for="(label, key) in intentLabelMap" :key="key" :label="label" :value="key" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" size="small" @click="handleFilter">查询</el-button>
              </el-form-item>
            </el-form>

            <el-table :data="tableData" v-loading="tableLoading" stripe style="width: 100%">
              <el-table-column prop="username" label="用户名" min-width="100" />
              <el-table-column prop="intent" label="意图" min-width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ getIntentLabel(row.intent) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="model" label="模型" min-width="120" />
              <el-table-column prop="promptTokens" label="输入Token" min-width="100" align="right" />
              <el-table-column prop="completionTokens" label="输出Token" min-width="100" align="right" />
              <el-table-column prop="totalTokens" label="总Token" min-width="100" align="right">
                <template #default="{ row }">
                  <span class="color-danger">{{ row.totalTokens }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="toolCalls" label="工具调用" min-width="80" align="center" />
              <el-table-column prop="latencyMs" label="耗时(ms)" min-width="90" align="right" />
              <el-table-column prop="createTime" label="时间" min-width="160" />
            </el-table>

            <el-pagination
              style="margin-top: 15px; justify-content: flex-end"
              v-model:current-page="pageNum"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50]"
              :total="tableTotal"
              layout="total, sizes, prev, pager, next, jumper"
              @current-change="handleTablePageChange"
              @size-change="handleTableSizeChange"
            />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.app-container {
  margin-top: 40px;
  margin-left: 120px;
  margin-right: 120px;
}

.summary-row {
  margin-bottom: 20px;
}

.summary-card {
  border: 1px solid #dcdfe6;
  padding: 20px;
  text-align: center;
}

.summary-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 8px;
}

.summary-sub {
  font-size: 12px;
  color: #c0c4cc;
}

.chart-row,
.ranking-row,
.detail-row {
  margin-bottom: 20px;
}

.out-border {
  border: 1px solid #dcdfe6;
}

.layout-title {
  color: #606266;
  padding: 15px 20px;
  background: #f2f6fc;
  font-weight: bold;
}

.color-primary {
  color: #409eff;
}

.color-success {
  color: #67c23a;
}

.color-warning {
  color: #e6a23c;
}

.color-danger {
  color: #f56c6c;
}
</style>
