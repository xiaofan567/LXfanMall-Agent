<template>
  <div class="app-container">
    <!-- 返回按钮 + 标题 -->
    <el-page-header @back="router.back()" style="margin-bottom: 20px">
      <template #content>
        <span class="page-title">{{ fileName }}</span>
      </template>
    </el-page-header>

    <!-- 文档信息卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>切片总数</span></template>
          <div class="stat-value">{{ detail.chunks_count }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>切割策略</span></template>
          <div class="stat-value">{{ strategyLabel }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>平均 Token</span></template>
          <div class="stat-value">{{ avgTokenCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>总字符数</span></template>
          <div class="stat-value">{{ totalChars }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索栏 -->
    <el-card style="margin-bottom: 20px">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-input
            v-model="searchText"
            placeholder="搜索切片内容..."
            clearable
            :prefix-icon="Search"
          />
        </el-col>
        <el-col :span="4">
          <span style="color: #909399; font-size: 14px">
            共 {{ filteredChunks.length }} / {{ detail.chunks_count }} 个切片
          </span>
        </el-col>
      </el-row>
    </el-card>

    <!-- 切片列表 -->
    <div v-loading="loading">
      <el-empty v-if="!loading && filteredChunks.length === 0" description="暂无切片数据" />

      <el-card
        v-for="chunk in filteredChunks"
        :key="chunk.id"
        class="chunk-card"
        shadow="hover"
      >
        <template #header>
          <div class="chunk-header">
            <div class="chunk-header-left">
              <el-tag type="primary" size="small">
                #{{ chunk.metadata?.chunk_index ?? '?' }}
              </el-tag>
              <span class="chunk-char-count">{{ chunk.content.length }} 字符</span>
            </div>
            <el-button
              type="primary"
              link
              size="small"
              @click="toggleExpand(chunk.id)"
            >
              {{ expandedSet.has(chunk.id) ? '收起' : '展开' }}
            </el-button>
          </div>
        </template>

        <div
          class="chunk-content"
          :class="{ 'chunk-content--collapsed': !expandedSet.has(chunk.id) }"
        >
          <pre class="chunk-text">{{ chunk.content }}</pre>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { getRagDocumentChunksAPI } from '@/apis/rag'
import type { RagChunk, RagDocumentDetail } from '@/apis/rag'

const route = useRoute()
const router = useRouter()

const fileName = ref(route.query.fileName as string)
const loading = ref(true)
const searchText = ref('')
const detail = reactive<RagDocumentDetail>({
  file_name: '',
  chunks_count: 0,
  chunks: [],
})

// 展开/收起状态
const expandedSet = reactive(new Set<string>())

function toggleExpand(id: string) {
  if (expandedSet.has(id)) {
    expandedSet.delete(id)
  } else {
    expandedSet.add(id)
  }
}

// 第一个切片的 metadata（用于展示文档级信息）
const firstChunkMeta = computed(() => detail.chunks[0]?.metadata ?? null)

// 策略标签映射
const STRATEGY_LABELS: Record<string, string> = {
  general: '通用分块',
  product: '商品文档',
  faq: '问答分块',
  manual: '手册分块',
  policy: '条款分块',
}

// 策略显示名
const strategyLabel = computed(() => {
  const key = firstChunkMeta.value?.chunk_strategy ?? firstChunkMeta.value?.strategy ?? ''
  return STRATEGY_LABELS[key] ?? key ?? '-'
})

// 平均 token 数
const avgTokenCount = computed(() => {
  if (!detail.chunks.length) return '-'
  const tokens = detail.chunks.reduce((sum, c) => sum + (c.metadata?.token_count ?? c.content.length), 0)
  return Math.round(tokens / detail.chunks.length)
})

// 总字符数
const totalChars = computed(() => {
  return detail.chunks.reduce((sum, c) => sum + c.content.length, 0)
})

// 搜索过滤 + 按 chunk_index 排序
const filteredChunks = computed(() => {
  const list = [...detail.chunks].sort(
    (a, b) => (a.metadata?.chunk_index ?? 0) - (b.metadata?.chunk_index ?? 0),
  )
  if (!searchText.value.trim()) return list
  const keyword = searchText.value.trim().toLowerCase()
  return list.filter((c) => c.content.toLowerCase().includes(keyword))
})

// 获取数据
async function fetchDetail() {
  if (!fileName.value) return
  loading.value = true
  try {
    const res = await getRagDocumentChunksAPI(fileName.value) as any
    if (res?.data) {
      detail.file_name = res.data.file_name
      detail.chunks_count = res.data.chunks_count
      detail.chunks = res.data.chunks ?? []
    }
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped>
.page-title {
  font-size: 18px;
  font-weight: 600;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  text-align: center;
}

.chunk-card {
  margin-bottom: 16px;
}

.chunk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chunk-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chunk-char-count {
  color: #909399;
  font-size: 13px;
}

.chunk-content {
  max-height: 600px;
  overflow-y: auto;
}

.chunk-content--collapsed {
  max-height: 120px;
  overflow: hidden;
  position: relative;
}

.chunk-content--collapsed::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: linear-gradient(transparent, #fff);
}

.chunk-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  font-family: 'Courier New', Courier, monospace;
}
</style>
