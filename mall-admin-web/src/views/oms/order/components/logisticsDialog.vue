<script setup lang="ts">
import { ref, watch } from 'vue'
import { getLogisticsAPI } from '@/apis/order'
import type { LogisticsTrace } from '@/types/order'

const props = defineProps({
  modelValue: Boolean,
  orderId: Number
})
const emit = defineEmits(['update:modelValue'])

// 弹窗显隐控制（直接代理 modelValue）
const dialogVisible = ref(false)
watch(() => props.modelValue, (val) => {
  dialogVisible.value = val
}, { immediate: true })
watch(dialogVisible, (val) => {
  emit('update:modelValue', val)
})

// 物流数据
const logisticsList = ref<LogisticsTrace[]>([])
const deliveryCompany = ref('')
const deliverySn = ref('')
const deliveryTime = ref('')
const receiverAddress = ref('')
const loading = ref(false)

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return ''
  return time.replace('T', ' ')
}

// 获取物流数据
const fetchLogistics = async () => {
  if (!props.orderId) return
  loading.value = true
  try {
    const res = await getLogisticsAPI(props.orderId)
    const data = res.data
    deliveryCompany.value = data.deliveryCompany || ''
    deliverySn.value = data.deliverySn || ''
    deliveryTime.value = data.deliveryTime || ''
    receiverAddress.value = data.receiverAddress || ''
    logisticsList.value = data.traceList || []
  } catch (error) {
    console.error('获取物流信息失败:', error)
    logisticsList.value = []
  } finally {
    loading.value = false
  }
}

// 打开弹窗时获取数据
watch(dialogVisible, (val) => {
  if (val) {
    fetchLogistics()
  }
})

// 关闭弹窗
const handleClose = () => {
  dialogVisible.value = false
}
</script>

<template>
  <el-dialog title="订单跟踪" v-model="dialogVisible" :before-close="handleClose" width="45%" destroy-on-close>
    <!-- 物流公司信息 -->
    <div v-if="deliveryCompany || deliverySn" style="margin-bottom: 20px; padding: 12px 16px; background: #f5f7fa; border-radius: 8px;">
      <div style="font-size: 14px; color: #303133;">
        <strong>{{ deliveryCompany }}</strong>
        <span style="color: #909399; margin-left: 8px;">{{ deliverySn }}</span>
      </div>
      <div v-if="deliveryTime" style="font-size: 12px; color: #909399; margin-top: 4px;">
        发货时间：{{ formatTime(deliveryTime) }}
      </div>
      <div v-if="receiverAddress" style="font-size: 12px; color: #909399; margin-top: 2px;">
        收件地址：{{ receiverAddress }}
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" style="text-align: center; padding: 40px 0; color: #909399;">
      加载中...
    </div>

    <!-- 物流轨迹时间线 -->
    <div v-else-if="logisticsList.length > 0">
      <el-steps direction="vertical" :active="logisticsList.length" finish-status="success" space="50px">
        <el-step
          v-for="(item, index) in logisticsList"
          :key="index"
          :title="item.statusText"
          :description="(item.location ? item.location + ' ' : '') + formatTime(item.traceTime)"
        ></el-step>
      </el-steps>
    </div>

    <!-- 空状态 -->
    <div v-else style="text-align: center; padding: 40px 0; color: #909399; font-size: 14px;">
      暂无物流信息
    </div>
  </el-dialog>
</template>

<style scoped>
</style>
