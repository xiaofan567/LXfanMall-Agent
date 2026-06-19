import http from '@/utils/http'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

// agent-service 直连实例（用于 mall-admin 未代理的接口）
const ragHttp = axios.create({
  baseURL: import.meta.env.VITE_AGENT_SERVICE_URL || 'http://localhost:8000',
  timeout: 5000,
})
ragHttp.interceptors.request.use((config) => {
  const token = useUserStore().userInfo.token
  if (token) config.headers.Authorization = token
  return config
})
ragHttp.interceptors.response.use(
  (res) => res.data?.data ?? res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.response?.data?.message || '请求失败'
    return Promise.reject(new Error(msg))
  },
)

// ── 类型定义 ──

export interface RagStrategy {
  key: string
  label: string
  description?: string
  type?: string
}

export interface RagDocument {
  file_name: string
  partition: string
  strategy: string
  upload_time: string
  doc_type: string
}

export interface RagUploadParams {
  file: File
  strategy: string
}

export interface RagStats {
  total_vectors: number
  total_documents: number
  collection_name: string
}

export interface RagDocListData {
  list: RagDocument[]
  total: number
  pageNum: number
  pageSize: number
}

export interface RagChunk {
  id: string
  content: string
  metadata: {
    chunk_index: number
    chunk_strategy?: string  // 新 chunker 策略名
    strategy?: string        // 旧 splitter 策略名（兼容）
    token_count?: number     // 新 chunker token 数
    chunk_size?: number      // 旧 splitter 块大小（兼容）
    chunk_overlap?: number   // 旧 splitter 重叠量（兼容）
    upload_time?: string
    [key: string]: any       // 允许其他元数据字段
  }
}

export interface RagDocumentDetail {
  file_name: string
  chunks_count: number
  chunks: RagChunk[]
}

// ── API 函数 ──

/** 上传文档并处理入库（直连 agent-service，避免 Java 后端丢失参数） */
export function uploadRagDocumentAPI(params: RagUploadParams) {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('chunking_strategy', params.strategy)
  formData.append('doc_type', params.strategy)

  return ragHttp<{ file_name: string; chunk_count: number }>({
    url: '/api/v1/rag/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}

/** 获取文档列表 */
export function getRagDocumentsAPI(params: { page: number; size: number }) {
  return http<RagDocListData>({
    url: '/rag/documents',
    method: 'get',
    params,
  })
}

/** 删除文档（直连 agent-service，避免 Java 代理超时） */
export function deleteRagDocumentAPI(fileName: string) {
  return ragHttp({
    url: `/api/v1/rag/documents/${encodeURIComponent(fileName)}`,
    method: 'delete',
    timeout: 30000,
  })
}

/** 获取分割策略列表 */
export function getRagStrategiesAPI() {
  return http<RagStrategy[]>({
    url: '/rag/strategies',
    method: 'get',
  })
}

/** 获取知识库统计 */
export function getRagStatsAPI() {
  return http<RagStats>({
    url: '/rag/stats',
    method: 'get',
  })
}

/** 获取文档切片详情（直接调用 agent-service） */
export function getRagDocumentChunksAPI(fileName: string) {
  return ragHttp<RagDocumentDetail>({
    url: `/api/v1/rag/documents/${encodeURIComponent(fileName)}/chunks`,
    method: 'get',
  })
}
