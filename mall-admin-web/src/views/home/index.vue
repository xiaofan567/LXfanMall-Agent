<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { dayjs } from 'element-plus'
import img_home_order from '@/assets/images/home_order.png'
import img_home_today_amount from '@/assets/images/home_today_amount.png'
import img_home_yesterday_amount from '@/assets/images/home_yesterday_amount.png'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import VChart from 'vue-echarts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
} from 'echarts/components'
import { getHomeSummaryAPI, getHomeChartAPI, getProductOverviewAPI, getMemberOverviewAPI } from '@/apis/home'
import type { HomeSummaryResult, HomeChartResult, HomeProductOverview, HomeMemberOverview } from '@/types/home'

// 通过use()方法按需注入ECharts的模块
use([
  CanvasRenderer, // 画布渲染器
  LineChart, // 折线图的绘制功能
  GridComponent, // 直角坐标系网格组件
  TooltipComponent, // 鼠标悬停时显示数据详情
  LegendComponent,  // 图例组件
  TitleComponent // 显示图表标题
])

// ── 首页数据 ──
const summaryData = ref<HomeSummaryResult | null>(null)
const productOverview = ref<HomeProductOverview | null>(null)
const memberOverview = ref<HomeMemberOverview | null>(null)
const summaryLoading = ref(true)

// ── 折线图 ──
const lineChartData = ref<HomeChartResult[]>([])
const chartLoading = ref(false)

// 日期选择器日期范围[start,end]
const datePickerRange = ref<Date[]>([])

// 初始化日期选择器为最近一周
const initDatePickerRange = () => {
  const end = new Date()
  const start = new Date(end.getTime() - 1000 * 60 * 60 * 24 * 7)
  datePickerRange.value = [start, end] as Date[]
}

// 获取折线图数据
const getLineChartData = async () => {
  chartLoading.value = true
  try {
    const startDate = dayjs(datePickerRange.value[0]).format('YYYY-MM-DD')
    const endDate = dayjs(datePickerRange.value[1]).format('YYYY-MM-DD')
    const res = await getHomeChartAPI({ startDate, endDate })
    lineChartData.value = res.data ?? []
  } catch (e) {
    console.error('获取折线图数据失败', e)
    lineChartData.value = []
  } finally {
    chartLoading.value = false
  }
}

// 获取汇总统计
const fetchSummary = async () => {
  try {
    const res = await getHomeSummaryAPI()
    summaryData.value = res.data
  } catch (e) {
    console.error('获取汇总统计失败', e)
  }
}

// 获取商品/用户总览
const fetchOverviews = async () => {
  try {
    const [prodRes, memberRes] = await Promise.all([
      getProductOverviewAPI(),
      getMemberOverviewAPI()
    ])
    productOverview.value = prodRes.data
    memberOverview.value = memberRes.data
  } catch (e) {
    console.error('获取总览数据失败', e)
  }
}

// 组件挂载成功初始化数据
onMounted(async () => {
  initDatePickerRange()
  // 并行加载所有数据
  await Promise.all([
    fetchSummary(),
    fetchOverviews(),
    getLineChartData()
  ])
  summaryLoading.value = false
})

// 日期选择器选项（基于当前日期动态计算）
const shortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 1000 * 60 * 60 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: '最近一月',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 1000 * 60 * 60 * 24 * 30)
      return [start, end]
    }
  }
]
// 处理日期范围变化
const handleDatePickerRangeChange = () => {
  getLineChartData()
}

// vue-charts 选项
const chartOption = computed(() => {
  const dates = lineChartData.value.map(item => item.date)
  const orderCounts = lineChartData.value.map(item => item.orderCount)
  const orderAmounts = lineChartData.value.map(item => item.orderAmount)
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLabel: {
        formatter: '{value}',
        rotate: 0
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '订单数量',
        position: 'left',
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '订单金额',
        position: 'right',
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '订单数量',
        type: 'line',
        areaStyle: {},
        data: orderCounts,
        smooth: true,
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '订单金额',
        type: 'line',
        yAxisIndex: 1,
        areaStyle: {},
        data: orderAmounts,
        smooth: true,
        itemStyle: {
          color: '#67C23A'
        }
      }
    ]
  }
})

// 格式化金额
const formatMoney = (val: number | undefined) => {
  if (val == null) return '￥0.00'
  return '￥' + val.toFixed(2)
}
</script>

<template>
  <div class="app-container" v-loading="summaryLoading">
    <div class="address-layout">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="out-border">
            <div class="layout-title">点Star支持项目</div>
            <div class="color-main address-content">
              <a href="https://github.com/macrozheng/mall" target="_blank">mall项目</a>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    <div class="total-layout">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="total-frame">
            <img :src="img_home_order" class="total-icon">
            <div class="total-title">今日订单总数</div>
            <div class="total-value">{{ summaryData?.todayOrderCount ?? 0 }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="total-frame">
            <img :src="img_home_today_amount" class="total-icon">
            <div class="total-title">今日销售总额</div>
            <div class="total-value">{{ formatMoney(summaryData?.todaySales) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="total-frame">
            <img :src="img_home_yesterday_amount" class="total-icon">
            <div class="total-title">昨日销售总额</div>
            <div class="total-value">{{ formatMoney(summaryData?.yesterdaySales) }}</div>
          </div>
        </el-col>
      </el-row>
    </div>
    <el-card class="mine-layout">
      <div style="text-align: center">
        <img width="140px" height="140px"
          src="http://macro-oss.oss-cn-shenzhen.aliyuncs.com/mall/banner/qrcode_for_macrozheng_258.jpg">
      </div>
      <div style="text-align: center">扫码关注作者<span class="color-main">公众号</span></div>
      <div style="text-align: center;margin-top: 5px">获取更多技术干货</div>
    </el-card>
    <div class="un-handle-layout">
      <div class="layout-title">待处理事务</div>
      <div class="un-handle-content">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="un-handle-item">
              <span class="font-medium">待付款订单</span>
              <span style="float: right" class="color-danger">({{ summaryData?.pendingPaymentCount ?? 0 }})</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="un-handle-item">
              <span class="font-medium">已完成订单</span>
              <span style="float: right" class="color-danger">({{ summaryData?.completedOrderCount ?? 0 }})</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="un-handle-item">
              <span class="font-medium">待确认收货订单</span>
              <span style="float: right" class="color-danger">({{ summaryData?.deliveredOrderCount ?? 0 }})</span>
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="un-handle-item">
              <span class="font-medium">待发货订单</span>
              <span style="float: right" class="color-danger">({{ summaryData?.pendingShipmentCount ?? 0 }})</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="un-handle-item">
              <span class="font-medium">新缺货登记</span>
              <span style="float: right" class="color-danger">(0)</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="un-handle-item">
              <span class="font-medium">待处理退款申请</span>
              <span style="float: right" class="color-danger">({{ summaryData?.pendingRefundCount ?? 0 }})</span>
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="un-handle-item">
              <span class="font-medium">已发货订单</span>
              <span style="float: right" class="color-danger">({{ summaryData?.shippedOrderCount ?? 0 }})</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="un-handle-item">
              <span class="font-medium">待处理退货订单</span>
              <span style="float: right" class="color-danger">({{ summaryData?.pendingReturnCount ?? 0 }})</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="un-handle-item">
              <span class="font-medium">广告位即将到期</span>
              <span style="float: right" class="color-danger">({{ summaryData?.adExpiringCount ?? 0 }})</span>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>
    <div class="overview-layout">
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="out-border">
            <div class="layout-title">商品总览</div>
            <div style="padding: 40px">
              <el-row>
                <el-col :span="6" class="color-danger overview-item-value">{{ productOverview?.delistedCount ?? 0 }}</el-col>
                <el-col :span="6" class="color-danger overview-item-value">{{ productOverview?.listedCount ?? 0 }}</el-col>
                <el-col :span="6" class="color-danger overview-item-value">{{ productOverview?.lowStockCount ?? 0 }}</el-col>
                <el-col :span="6" class="color-danger overview-item-value">{{ productOverview?.totalCount ?? 0 }}</el-col>
              </el-row>
              <el-row class="font-medium">
                <el-col :span="6" class="overview-item-title">已下架</el-col>
                <el-col :span="6" class="overview-item-title">已上架</el-col>
                <el-col :span="6" class="overview-item-title">库存紧张</el-col>
                <el-col :span="6" class="overview-item-title">全部商品</el-col>
              </el-row>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="out-border">
            <div class="layout-title">用户总览</div>
            <div style="padding: 40px">
              <el-row>
                <el-col :span="6" class="color-danger overview-item-value">{{ memberOverview?.todayNewCount ?? 0 }}</el-col>
                <el-col :span="6" class="color-danger overview-item-value">{{ memberOverview?.yesterdayNewCount ?? 0 }}</el-col>
                <el-col :span="6" class="color-danger overview-item-value">{{ memberOverview?.monthNewCount ?? 0 }}</el-col>
                <el-col :span="6" class="color-danger overview-item-value">{{ memberOverview?.totalCount ?? 0 }}</el-col>
              </el-row>
              <el-row class="font-medium">
                <el-col :span="6" class="overview-item-title">今日新增</el-col>
                <el-col :span="6" class="overview-item-title">昨日新增</el-col>
                <el-col :span="6" class="overview-item-title">本月新增</el-col>
                <el-col :span="6" class="overview-item-title">会员总数</el-col>
              </el-row>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    <div class="statistics-layout">
      <div class="layout-title">订单统计</div>
      <el-row>
        <el-col :span="4">
          <div style="padding: 20px">
            <div>
              <div style="color: #909399;font-size: 14px">本月订单总数</div>
              <div style="color: #606266;font-size: 24px;padding: 10px 0">{{ summaryData?.monthlyOrderCount ?? 0 }}</div>
              <div>
                <span :class="summaryData?.monthlyOrderGrowth?.startsWith('+') ? 'color-success' : 'color-danger'"
                  style="font-size: 14px">{{ summaryData?.monthlyOrderGrowth ?? '0%' }}</span>
                <span style="color: #C0C4CC;font-size: 14px">同比上月</span>
              </div>
            </div>
            <div style="margin-top: 20px;">
              <div style="color: #909399;font-size: 14px">本周订单总数</div>
              <div style="color: #606266;font-size: 24px;padding: 10px 0">{{ summaryData?.weeklyOrderCount ?? 0 }}</div>
              <div>
                <span :class="summaryData?.weeklyOrderGrowth?.startsWith('+') ? 'color-success' : 'color-danger'"
                  style="font-size: 14px">{{ summaryData?.weeklyOrderGrowth ?? '0%' }}</span>
                <span style="color: #C0C4CC;font-size: 14px">同比上周</span>
              </div>
            </div>
            <div style="margin-top: 20px;">
              <div style="color: #909399;font-size: 14px">本月销售总额</div>
              <div style="color: #606266;font-size: 24px;padding: 10px 0">{{ formatMoney(summaryData?.monthlySales) }}</div>
              <div>
                <span :class="summaryData?.monthlySalesGrowth?.startsWith('+') ? 'color-success' : 'color-danger'"
                  style="font-size: 14px">{{ summaryData?.monthlySalesGrowth ?? '0%' }}</span>
                <span style="color: #C0C4CC;font-size: 14px">同比上月</span>
              </div>
            </div>
            <div style="margin-top: 20px;">
              <div style="color: #909399;font-size: 14px">本周销售总额</div>
              <div style="color: #606266;font-size: 24px;padding: 10px 0">{{ formatMoney(summaryData?.weeklySales) }}</div>
              <div>
                <span :class="summaryData?.weeklySalesGrowth?.startsWith('+') ? 'color-success' : 'color-danger'"
                  style="font-size: 14px">{{ summaryData?.weeklySalesGrowth ?? '0%' }}</span>
                <span style="color: #C0C4CC;font-size: 14px">同比上周</span>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="20">
          <div style="padding: 10px;border-left:1px solid #DCDFE6">
            <el-date-picker style="float: right;z-index: 1" size="small" v-model="datePickerRange" type="daterange"
              align="right" unlink-panels range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期"
              :shortcuts="shortcuts" @change="handleDatePickerRangeChange">
            </el-date-picker>
            <div style="height: 400px;">
              <v-chart v-if="!chartLoading" :option="chartOption" autoresize />
              <div v-else
                style="display: flex; justify-content: center; align-items: center; height: 100%;width: 100%;">
                <el-skeleton :rows="5" animated />
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  margin-top: 40px;
  margin-left: 120px;
  margin-right: 120px;
}

.total-layout {
  margin-top: 20px;
}

.total-frame {
  border: 1px solid #DCDFE6;
  padding: 20px;
  height: 100px;
}

.total-icon {
  color: #409EFF;
  width: 60px;
  height: 60px;
}

.total-title {
  position: relative;
  font-size: 16px;
  color: #909399;
  left: 70px;
  top: -50px;
}

.total-value {
  position: relative;
  font-size: 18px;
  color: #606266;
  left: 70px;
  top: -40px;
}

.un-handle-layout {
  margin-top: 20px;
  border: 1px solid #DCDFE6;
}

.layout-title {
  color: #606266;
  padding: 15px 20px;
  background: #F2F6FC;
  font-weight: bold;
}

.un-handle-content {
  padding: 20px 40px;
}

.un-handle-item {
  border-bottom: 1px solid #EBEEF5;
  padding: 10px;
}

.overview-layout {
  margin-top: 20px;
}

.overview-item-value {
  font-size: 24px;
  text-align: center;
}

.overview-item-title {
  margin-top: 10px;
  text-align: center;
}

.out-border {
  border: 1px solid #DCDFE6;
}

.statistics-layout {
  margin-top: 20px;
  border: 1px solid #DCDFE6;
}

.mine-layout {
  position: absolute;
  right: 140px;
  top: 107px;
  width: 250px;
  height: 235px;
}

.address-content {
  padding: 20px;
  font-size: 18px
}
</style>
