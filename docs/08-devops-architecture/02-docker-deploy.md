# Docker 与部署

> 所属模块：`08-devops-architecture` · 部署、运维与软件架构  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/08-devops-architecture/02-docker-deploy.md`](../../exercises/08-devops-architecture/02-docker-deploy.md)

## 本章定位

- **本章角色**：理解镜像/容器；会写 Dockerfile；会用 Compose 编排 API + DB + Redis。
- **和 Agent**：本地一键起依赖；部署到服务器时环境一致。

## 学习目标

1. 分清镜像与容器。
2. 为 FastAPI 应用写可用 Dockerfile。
3. 用 Compose 编排多服务。
4. 了解多阶段构建与环境隔离；K8s 仅扫盲。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 镜像/容器、Dockerfile、compose | 能本地编排跑通 |
| **建议掌握** | 多阶段构建、环境隔离 | 镜像更小更安全 |
| **了解即可** | K8s 扫盲 | 地图 |

---

## 1. 镜像 vs 容器

```text
镜像 image = 只读模板（含代码/依赖/系统层）
容器 container = 镜像的运行实例
```

```bash
docker pull postgres:16
docker images
docker run --name pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16
docker ps
docker logs -f pg
docker stop pg
docker rm pg
```

---

## 2. 必掌握：Dockerfile（FastAPI 示例）

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app

# 推荐：把本地包装进镜像（需 pyproject 可构建）
# RUN pip install --no-cache-dir .
# 最小示意（仅演示跑通时）也可直接装运行时依赖——此时不要假设 pip 已安装你的包名：
RUN pip install --no-cache-dir "fastapi" "uvicorn[standard]"

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
# 因上面 COPY 了 ./app，uvicorn 靠 PYTHONPATH=/app 的父目录工作区即可找到包
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建与运行：

```bash
docker build -t my-agent-api:dev .
docker run --rm -p 8000:8000 -e APP_API_KEY=dev my-agent-api:dev
```

注意：

- 监听 `0.0.0.0` 才能从容器外访问
- 密钥用 `-e` / compose `env_file`，别写进镜像层
- `.dockerignore` 排除 `.venv`、`.git`、`__pycache__`

---

## 3. 必掌握：Compose 本地编排

`compose.yaml` 示意：

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/agent  # SQLAlchemy 方言 URL
      REDIS_URL: redis://redis:6379/0
      APP_API_KEY: dev-key
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: agent
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d agent"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

```bash
docker compose up --build
docker compose down
```

服务间主机名用 **服务名**（`db`、`redis`），不是 `localhost`。  
`depends_on` 默认只保证**容器已启动**，不保证 Postgres 已可连；上面用 `healthcheck` + `condition: service_healthy` 避免 API 抢连失败。

---

## 4. 建议掌握：多阶段构建与隔离

多阶段：构建阶段装编译依赖，运行阶段只拷贝产物 → 镜像更小、攻击面更小。

环境隔离：

| 环境 | 做法 |
|------|------|
| 本地 | compose + `.env` |
| 预发/生产 | 不同 tag、不同密钥、不同 DB |

同一镜像，不同配置；**十二要素**思想：配置进环境，不进代码。

---

## 5. 了解即可：K8s

Pod / Service / Deployment / Ingress……云上规模化编排。  
个人项目 compose 足够；入职后再学 K8s 不迟。

---

## 6. 常见坑

1. 应用连 `localhost:5432`（在容器里 localhost 是自己）
2. 把密钥 `ENV` 写死在 Dockerfile 并推送仓库
3. 镜像塞进 `.venv` 导致巨大且错误
4. 数据卷忘记挂载，`compose down -v` 丢库

---

## 7. 练习指引

[`exercises/08-devops-architecture/02-docker-deploy.md`](../../exercises/08-devops-architecture/02-docker-deploy.md)

---

## 8. 小结与下一站

### 自检

- [ ] 能解释镜像/容器差异
- [ ] 能写并构建简单 Dockerfile
- [ ] 能读懂 compose 多服务与网络名

### 下一章

[`03-software-architecture.md`](./03-software-architecture.md) —— 分层与边界，避免 Agent 变成大泥球。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Linux 基础](./01-linux-basics.md)
- 下一章：[软件架构基础](./03-software-architecture.md)
