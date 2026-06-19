<template>
  <div class="app-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>向量总数</span>
          </template>
          <div class="stat-value">{{ stats.total_vectors }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>集合名称</span>
          </template>
          <div class="stat-value">{{ stats.collection_name }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>文档总数</span>
          </template>
          <div class="stat-value">{{ stats.total_documents }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作栏 -->
    <el-card style="margin-bottom: 20px">
      <el-button type="primary" @click="handleUpload">
        <el-icon><Upload /></el-icon>
        上传文档
      </el-button>
    </el-card>

    <!-- 数据表格 -->
    <el-card>
      <el-table :data="list" v-loading="listLoading" border style="width: 100%">
        <el-table-column label="文件名" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewDetail(row)">{{ row.file_name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="切割策略" prop="strategy" width="140">
          <template #default="{ row }">
            <el-tag>{{ strategyLabel(row.strategy) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上传时间" prop="upload_time" width="180" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row)">详情</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        style="margin-top: 16px; justify-content: flex-end"
        v-model:current-page="listQuery.page"
        v-model:page-size="listQuery.size"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="dialogVisible" title="上传知识文档" width="500px">
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            drag
          >
            <el-icon class="el-icon--upload"><Upload /></el-icon>
            <div class="el-upload__text">拖拽文件到此处，或 <em>点击选择</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 .txt .pdf .docx .xlsx .md .csv，最大 20MB</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="切割策略">
          <el-select v-model="uploadForm.strategy" style="width: 100%">
            <el-option
              v-for="s in strategies"
              :key="s.key"
              :label="s.label"
              :value="s.key"
            >
              <span>{{ s.label }}</span>
              <span v-if="s.description" style="float: right; color: #8492a6; font-size: 12px">{{ s.description }}</span>
            </el-option>
          </el-select>
        </el-form-item>


      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">
          确认上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'
import {
  uploadRagDocumentAPI,
  getRagDocumentsAPI,
  deleteRagDocumentAPI,
  getRagStrategiesAPI,
  getRagStatsAPI,
} from '@/apis/rag'
import type { RagStrategy, RagDocument, RagStats } from '@/apis/rag'

const router = useRouter()

// ── 列表数据 ──
const list = ref<RagDocument[]>([])
const total = ref(0)
const listLoading = ref(true)
const listQuery = reactive({ page: 1, size: 10 })

// ── 统计数据 ──
const stats = ref<RagStats>({ total_vectors: 0, total_documents: 0, collection_name: '-' })

// ── 策略列表 ──
const strategies = ref<RagStrategy[]>([])

// ── 上传对话框 ──
const dialogVisible = ref(false)
const uploading = ref(false)
const selectedFile = ref<File | null>(null)
const uploadForm = reactive({
  strategy: 'general',
})

// ── 获取列表 ──
async function getList() {
  listLoading.value = true
  try {
    const res = await getRagDocumentsAPI(listQuery)
    list.value = res.data?.list ?? []
    total.value = res.data?.total ?? 0
  } catch {
    list.value = []
    total.value = 0
  } finally {
    listLoading.value = false
  }
}

// ── 获取统计 ──
async function getStats() {
  try {
    const res = await getRagStatsAPI()
    if (res.data) stats.value = res.data
  } catch {
    // ignore
  }
}

// ── 获取策略列表 ──
async function getStrategies() {
  try {
    const res = await getRagStrategiesAPI()
    if (res.data) strategies.value = res.data
  } catch {
    // ignore
  }
}

// ── 策略标签（兼容新旧两套策略名）──
const STRATEGY_LABELS: Record<string, string> = {
  // 新 ChunkerFactory 策略
  general: '通用分块',
  product: '商品文档',
  faq: '问答分块',
  manual: '手册分块',
  policy: '条款分块',

}

function strategyLabel(key: string): string {
  return STRATEGY_LABELS[key] ?? strategies.value.find((s) => s.key === key)?.label ?? key
}

// ── 分页 ──
function handleSizeChange(val: number) {
  listQuery.page = 1
  listQuery.size = val
  getList()
}
function handleCurrentChange(val: number) {
  listQuery.page = val
  getList()
}

// ── 上传 ──
function handleUpload() {
  selectedFile.value = null
  uploadForm.strategy = 'general'
  dialogVisible.value = true
}

function handleFileChange(file: UploadFile) {
  selectedFile.value = file.raw ?? null
}
function handleFileRemove() {
  selectedFile.value = null
}

async function submitUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  const fileName = selectedFile.value.name
  // 校验同名文件
  const exists = list.value.some((d) => d.file_name === fileName)
  if (exists) {
    try {
      await ElMessageBox.confirm(
        `知识库中已存在文档「${fileName}」，是否覆盖？`,
        '文件已存在',
        { confirmButtonText: '覆盖', cancelButtonText: '取消', type: 'warning' },
      )
    } catch {
      return // 用户点了取消
    }
  }
  console.log('[RAG Upload] strategy =', uploadForm.strategy)
  uploading.value = true
  try {
    const res = await uploadRagDocumentAPI({
      file: selectedFile.value,
      strategy: uploadForm.strategy,
    })
    ElMessage.success(`上传成功，共 ${res?.chunk_count ?? 0} 个分块`)
    dialogVisible.value = false
    getList()
    getStats()
  } catch {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

// ── 删除 ──
async function handleDelete(row: RagDocument) {
  try {
    await ElMessageBox.confirm(`确定删除文档「${row.file_name}」？`, '提示', {
      type: 'warning',
    })
    await deleteRagDocumentAPI(row.file_name)
    ElMessage.success('删除成功')
    getList()
    getStats()
  } catch {
    // cancelled or failed
  }
}

// ── 查看详情 ──
function handleViewDetail(row: RagDocument) {
  router.push({ path: '/ai/knowledgeDetail', query: { fileName: row.file_name } })
}

// ── 初始化 ──
onMounted(() => {
  getList()
  getStats()
  getStrategies()
})
</script>

<style scoped>
.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  text-align: center;
}
</style>
