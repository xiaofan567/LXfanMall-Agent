"""RAG 管理 API — 文档上传、列表、删除、策略查询。"""

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.api.v1.deps import CurrentUser, require_admin, require_user
from app.config.settings import get_settings
from app.core.limiter import limiter
from app.rag.chunker import ChunkerFactory
from app.rag.document_service import RAGDocumentService
from app.rag.vector_store import MilvusVectorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])

# 延迟初始化，避免导入时连接 Milvus
_doc_service: RAGDocumentService | None = None
_vector_store: MilvusVectorStore | None = None

# 策略描述（新增分块策略使用）
_STRATEGY_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "general": {
        "label": "通用分块",
        "description": "类似 RAGFlow naive 策略，按段落合并，适用于通用文档",
    },
    "product": {
        "label": "商品文档分块",
        "description": "保留规格表格和商品描述，适用于商品说明文档",
    },
    "faq": {
        "label": "问答分块",
        "description": "Q&A 对不拆分，适用于 FAQ / 常见问题",
    },
    "manual": {
        "label": "手册分块",
        "description": "按章节 / 步骤切分，适用于手册 / 指南",
    },
    "policy": {
        "label": "条款分块",
        "description": "按条款边界切分，适用于政策 / 协议 / 规则",
    },
}


def _get_doc_service() -> RAGDocumentService:
    global _doc_service
    if _doc_service is None:
        _doc_service = RAGDocumentService()
    return _doc_service


def _get_vector_store() -> MilvusVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = MilvusVectorStore()
    return _vector_store


@router.post("/upload")
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    chunking_strategy: str = Form("general"),
    doc_type: str | None = Form(None),
    _user: CurrentUser = Depends(require_user),
):
    """上传文件 → 解析 → 分块 → Embedding → 入库 Milvus。

    参数:
      - chunking_strategy: 分块策略名（general/product/faq/manual/policy），默认 general。
      - doc_type: 文档类型标签，传入时写入切片元数据。
    """
    settings = get_settings()

    # 校验文件类型白名单
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".html", ".xlsx"}
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"不支持的文件类型: {ext}。允许的类型: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # 校验文件大小
    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            400,
            f"文件大小超过限制 ({settings.max_upload_size // 1024 // 1024}MB)",
        )

    # 校验策略
    logger.info("上传请求接收 | file=%s chunking_strategy=%s doc_type=%s", file.filename, chunking_strategy, doc_type)
    if chunking_strategy not in ChunkerFactory.CHUNKER_MAP:
        raise HTTPException(400, f"未知分割策略: {chunking_strategy}")

    try:
        doc_service = _get_doc_service()
        result = await doc_service.upload_document(
            file_name=file.filename,
            file_content=content,
            chunking_strategy=chunking_strategy,
            doc_type=doc_type,
        )
        return {"code": 200, "message": "上传处理成功", "data": result}
    except Exception as e:
        logger.exception("文档处理失败")
        raise HTTPException(500, "文档处理失败，请稍后重试")


@router.get("/documents")
async def list_documents(page: int = 1, size: int = 20):
    """文档列表（基于 Milvus doc_id 去重）。"""
    try:
        store = _get_vector_store()
        documents = await store.list_documents()
        # 分页
        total = len(documents)
        start = (page - 1) * size
        end = start + size
        return {
            "code": 200,
            "data": {
                "list": documents[start:end],
                "total": total,
                "pageNum": page,
                "pageSize": size,
            },
        }
    except Exception as e:
        logger.exception("获取文档列表失败")
        raise HTTPException(500, "获取文档列表失败，请稍后重试")


@router.delete("/documents/{file_name}")
async def delete_document(
    file_name: str,
    _user: CurrentUser = Depends(require_admin),
):
    """删除文档及其所有向量切片。"""
    try:
        await _get_vector_store().delete_by_name(file_name)
        return {"code": 200, "message": "删除成功"}
    except Exception as e:
        logger.exception("删除文档失败")
        raise HTTPException(500, "删除文档失败，请稍后重试")


@router.get("/documents/{file_name}/chunks")
async def get_document_chunks(
    file_name: str,
):
    """获取指定文档的所有切片内容。"""
    try:
        chunks = await _get_vector_store().get_chunks_by_file_name(file_name)
        if not chunks:
            raise HTTPException(404, "文档不存在或无切片数据")
        return {
            "code": 200,
            "data": {
                "file_name": file_name,
                "chunks_count": len(chunks),
                "chunks": chunks,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("获取文档切片失败")
        raise HTTPException(500, "获取文档切片失败，请稍后重试")


@router.post("/documents/{file_name}/reprocess")
async def reprocess_document(
    file_name: str,
    new_strategy: str = Form(...),
    _user: CurrentUser = Depends(require_admin),
):
    """使用新策略重新处理已入库文档。

    流程：获取现有切片内容 → 删除旧切片 → 新策略重新分块 → 重新 Embedding 入库。
    """
    try:
        # 校验策略
        if new_strategy not in ChunkerFactory.CHUNKER_MAP:
            raise HTTPException(400, f"未知分割策略: {new_strategy}")

        result = await _get_doc_service().reprocess_document(
            file_name=file_name,
            new_strategy=new_strategy,
        )
        return {"code": 200, "message": "重新处理成功", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("文档重新处理失败")
        raise HTTPException(500, "文档重新处理失败，请稍后重试")


@router.get("/strategies")
async def get_strategies():
    """获取可用的文本分割策略。"""
    strategies = []

    for key in ChunkerFactory.CHUNKER_MAP:
        info = _STRATEGY_DESCRIPTIONS.get(key, {})
        strategies.append({
            "key": key,
            "label": info.get("label", key),
            "description": info.get("description", ""),
        })

    return {"code": 200, "data": strategies}


@router.get("/stats")
async def get_stats():
    """知识库统计。"""
    store = _get_vector_store()
    count = await store.count()
    partitions = store.list_partitions()
    settings = get_settings()
    return {
        "code": 200,
        "data": {
            "total_vectors": count,
            "total_documents": len(partitions),
            "collection_name": settings.milvus_collection,
        },
    }
