# LXfanMall 部署指南

## 前置条件

- 服务器: 腾讯云轻量 4核4G + OpenCloudOS9 + 宝塔
- 已安装: Docker + Docker Compose + Git
- Swap: 4G (已配好)

## 项目结构

```
deploy/
├── docker-compose.yml          # 主编排文件（基础设施 + 应用 + Nginx）
├── mall.env                    # Java 应用环境变量
├── agent-service.env           # Python AI 服务环境变量
├── nginx/nginx.conf            # Nginx 配置
├── mall-admin/Dockerfile       # mall-admin 构建配置
├── mall-portal/Dockerfile      # mall-portal 构建配置
├── mall-search/Dockerfile      # mall-search 构建配置
└── data/                       # 持久化数据目录（自动生成）
    ├── mysql/data
    ├── redis/data
    ├── mongo/db
    ├── rabbitmq/data
    ├── elasticsearch/data
    ├── elasticsearch/plugins
    ├── milvus
    ├── minio/data
    ├── nginx/html/c            # C 端前端
    ├── nginx/html/admin        # B 端前端
    ├── agent-uploads
    └── logs/                   # 各服务日志
```

## 服务架构

| 服务 | 端口 | 说明 |
|------|------|------|
| **基础设施** | | |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |
| MongoDB | 27017 | 会话存储 |
| RabbitMQ | 5672/15672 | 消息队列 |
| Elasticsearch | 9200 | 搜索引擎 |
| Milvus | 19530 | 向量数据库 |
| MinIO | 9090/9001 | 对象存储 |
| **Java 应用** | | |
| mall-admin | 8080 | 管理后台 API |
| mall-portal | 8085 | C 端 API |
| mall-search | 8081 | 搜索服务 |
| **Python 服务** | | |
| agent-service | 8000 | AI 智能体 |
| **Nginx** | | |
| C 端 | 80 | 前端 + API 代理 |
| B 端 | 8080 | 管理后台前端 |

## 部署步骤

### 1. 本地打包 Java (Windows)

```powershell
cd D:\claude\mall\mall
mvn clean package -DskipTests
```

### 2. 上传文件到服务器

```bash
# 上传 jar 包
scp mall-admin/target/mall-admin-1.0-SNAPSHOT.jar   root@IP:/opt/mall/deploy/mall-admin/
scp mall-search/target/mall-search-1.0-SNAPSHOT.jar  root@IP:/opt/mall/deploy/mall-search/
scp mall-portal/target/mall-portal-1.0-SNAPSHOT.jar  root@IP:/opt/mall/deploy/mall-portal/

# 上传整个 deploy 目录
scp -r deploy/ root@IP:/opt/mall/
```

### 3. 前端打包上传

```bash
# C 端
cd LXfanMallWeb
npm run build
scp -r dist/* root@IP:/opt/mall/deploy/data/nginx/html/c/

# B 端
cd mall-admin-web
npm run build
scp -r dist/* root@IP:/opt/mall/deploy/data/nginx/html/admin/
```

### 4. 配置环境变量

```bash
cd /opt/mall/deploy

# 编辑 Java 应用配置
vi mall.env

# 编辑 AI 服务配置（必须填写 API Key）
vi agent-service.env
```

**mall.env 配置项：**
```env
MYSQL_ROOT_PASSWORD=root          # MySQL 密码
ALIPAY_APP_ID=                    # 支付宝 AppID
ALIPAY_PUBLIC_KEY=                # 支付宝公钥
ALIPAY_PRIVATE_KEY=               # 支付宝私钥
ALIYUN_SMS_ENABLED=false          # 是否启用短信
```

**agent-service.env 配置项：**
```env
LLM_API_KEY=                      # DeepSeek API Key（必填）
EMBEDDING_API_KEY=                # DashScope API Key（必填）
RERANKER_API_KEY=                 # DashScope API Key（必填）
```

### 5. 启动服务

```bash
cd /opt/mall/deploy

# 一键启动所有服务
docker compose up -d --build

# 查看启动状态
docker compose ps

# 查看日志
docker compose logs -f mall-portal
```

### 6. 首次部署初始化

```bash
# 1. 同步 ES 数据（必须）
curl -X POST http://localhost:8081/esProduct/importAll

# 2. 创建 MinIO Bucket
# 访问 http://IP:9001，创建 mall bucket

# 3. 创建 RabbitMQ vhost
# 访问 http://IP:15672，创建 /mall vhost 和 mall 用户

# 4. 导入数据库（如有）
mysql -h127.0.0.1 -P3306 -uroot -proot mall < mall.sql
```

## 常用命令

```bash
# 启动全部
docker compose up -d

# 停止全部
docker compose down

# 重建某个服务
docker compose up -d --build mall-portal

# 查看某个服务日志
docker compose logs -f agent-service

# 进入容器排查
docker exec -it mall-portal /bin/bash

# 重启单个服务
docker compose restart redis
```

## Nginx 配置说明

- **C 端 (端口 80)**: `/api/` 代理到 mall-portal:8085，`/search-api/` 代理到 mall-search:8081，`/agent-api/` 代理到 agent-service:8000
- **B 端 (端口 8080)**: `/api/` 代理到 mall-admin:8080，`/rag/` 代理到 RAG 知识库接口
- **演示模式**: 默认拦截写操作（POST/PUT/DELETE），仅放行登录/登出/支付回调
- **图片代理**: OSS 优先，MinIO 兜底

## 注意事项

1. **ES 索引同步**: 首次部署后必须手动触发 `POST /esProduct/importAll`
2. **MinIO Bucket**: 首次需要在 MinIO Console (端口 9001) 创建 `mall` bucket
3. **RabbitMQ**: 需要先在管理界面 (端口 15672) 创建 `/mall` vhost 和 `mall` 用户
4. **MySQL 数据**: 如果有初始 SQL，需要导入到 3306 端口的 mall 数据库
5. **防火墙**: 宝塔安全组需放行 80, 8080, 3306, 6379, 9200, 15672, 19530, 9090, 9001 端口
6. **内存限制**: 4G 内存建议配置 Swap 4G，Milvus 限制 1G 内存
