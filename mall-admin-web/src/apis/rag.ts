import http from '@/utils/http'

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
    chunk_strategy?: string
    strategy?: string
    token_count?: number
    chunk_size?: number
    chunk_overlap?: number
    upload_time?: string
    [key: string]: any
  }
}

export interface RagDocumentDetail {
  file_name: string
  chunks_count: number
  chunks: RagChunk[]
}

// ── API 函数（全部走 mall-admin 代理） ──

/** 上传文档并处理入库 */
export function uploadRagDocumentAPI(params: RagUploadParams) {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('strategy', params.strategy)

  return http<{ file_name: string; chunk_count: number }>({
    url: '/rag/upload',
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

/** 删除文档 */
export function deleteRagDocumentAPI(fileName: string) {
  return http({
    url: `/rag/documents/${encodeURIComponent(fileName)}`,
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

/** 获取文档切片详情 */
export function getRagDocumentChunksAPI(fileName: string) {
  return http<RagDocumentDetail>({
    url: `/rag/documents/${encodeURIComponent(fileName)}/chunks`,
    method: 'get',
  })
}
