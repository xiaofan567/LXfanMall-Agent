# AI Agent 服务说明

本文档详细说明 agent-service 的配置、架构和使用方式。

## 一、服务架构

```
用户消息 → FastAPI → LangGraph 工作流
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
        意图分类     工具调用     RAG 检索
        (DeepSeek)  (电商API)   (Milvus)
            │           │           │
            └───────────┼───────────┘
                        ▼
                    生成回复 → SSE 流式输出
```

## 二、环境变量配置

在 `agent-service/.env` 中配置（参考 `.env.example`）：

### LLM 配置（必需）

```env
LLM_API_KEY=sk-xxx          # DeepSeek API Key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

申请地址：https://platform.deepseek.com/

### Embedding 配置（RAG 必需）

```env
EMBEDDING_API_KEY=sk-xxx    # 阿里云 DashScope API Key
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v4
```

申请地址：https://dashscope.console.aliyun.com/

### Reranker 配置（RAG 必需）

```env
RERANKER_API_KEY=sk-xxx     # 同上，可共用同一个 Key
RERANKER_BASE_URL=https://dashscope.aliyuncs.com/api/v1
RERANKER_MODEL=gte-rerank-v2
```

### 后端地址

```env
MALL_PORTAL_URL=http://localhost:8085   # Java 前台 API
MALL_SEARCH_URL=http://localhost:8081   # Java 搜索服务
JWT_SECRET=mall-portal-secret           # 必须与 Java 后端一致
ADMIN_JWT_SECRET=mall-admin-secret      # 必须与 Java 后端一致
```

### Milvus 配置

```env
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=LXfanmall_knowledge
MILVUS_DIMENSION=1024
```

### Redis 配置

```env
RAG_REDIS_URL=redis://localhost:6379/2      # RAG 查询缓存
SESSION_REDIS_URL=redis://localhost:6379/3   # 会话记忆
SESSION_TTL=3600                              # 会话过期时间（秒）
SESSION_MAX_TURNS=20                          # 最大对话轮数
```

## 三、核心模块

### 1. LangGraph 工作流

入口：`app/agent/graph.py`

工作流程：
1. **意图分类**：LLM 分析用户消息，判断意图类型
2. **路由决策**：根据意图选择执行路径
3. **工具调用**：调用电商 API 完成操作
4. **RAG 检索**：从知识库检索相关信息
5. **回复生成**：LLM 生成自然语言回复

支持的意图类型：
- `product_recommend` — 商品推荐
- `order_query` — 订单查询
- `cart_operation` — 购物车操作
- `product_review` — 商品评价
- `faq` — 常见问题（走 RAG）
- `chitchat` — 闲聊

### 2. 工具集

入口：`app/agent/tools.py`

| 工具名 | 功能 | 调用的后端 API |
|--------|------|---------------|
| `search_product` | 商品搜索 | GET /search-api/product |
| `get_product_detail` | 商品详情 | GET /product/{id} |
| `get_order_list` | 订单列表 | GET /order/list |
| `get_cart` | 查看购物车 | GET /cart/list |
| `add_to_cart` | 加入购物车 | POST /cart/add |
| `submit_review` | 提交评价 | POST /comment/create |

### 3. RAG 检索引擎

入口：`app/rag/engine.py`

流程：
1. **文档上传**：用户上传 PDF/Word/Excel/HTML/Markdown
2. **文档解析**：deepdoc 模块解析各格式
3. **文本分块**：按策略切分（general/product/faq/manual/policy）
4. **向量嵌入**：调用 Qwen text-embedding-v4
5. **存入 Milvus**：向量 + 元数据
6. **检索时**：查询向量化 → Milvus 检索 → Reranker 重排序

### 4. 安全防护

- **速率限制**：基于 IP 的请求频率控制
- **破坏性操作确认**：删除购物车、取消订单需二次确认
- **注入防护**：Milvus 查询参数化
- **权限校验**：admin 接口 JWT 验证

## 四、API 接口

### 流式对话

```
POST /api/v1/chat/stream
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "message": "帮我推荐一款项链",
  "session_id": "可选，不传则新建会话"
}

Response: text/event-stream
data: {"type": "token", "content": "好的"}
data: {"type": "tool_call", "tool": "search_product", "args": {...}}
data: {"type": "tool_result", "result": [...]}
data: {"type": "token", "content": "为您推荐以下商品..."}
data: {"type": "done", "session_id": "xxx", "intent": "product_recommend"}
```

### RAG 管理

```
POST   /api/v1/rag/upload                      # 上传文档
GET    /api/v1/rag/documents                    # 文档列表
GET    /api/v1/rag/documents/{name}/chunks      # 文档切片
DELETE /api/v1/rag/documents/{name}             # 删除文档
POST   /api/v1/rag/documents/{name}/reprocess   # 重新处理
GET    /api/v1/rag/strategies                   # 分块策略列表
GET    /api/v1/rag/stats                        # 知识库统计
```

## 五、启动与调试

```bash
cd agent-service

# 安装依赖
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 启动
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 运行测试
pytest
```

## 六、Token 用量统计

Agent 会自动采集每次对话的 Token 消耗：

- **采集**：通过 LangChain Callback 记录 prompt_tokens 和 completion_tokens
- **上报**：定期批量写入 Java 后端的 `ums_token_usage` 表
- **查看**：管理后台 → Token 用量统计页面

上报接口：
```
POST http://localhost:8080/tokenUsage/report
Content-Type: application/json

[
  {
    "username": "admin",
    "session_id": "xxx",
    "intent": "product_recommend",
    "model": "deepseek-chat",
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350,
    "tool_calls": 1,
    "latency_ms": 2500
  }
]
```
