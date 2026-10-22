# 练习：Docker 与部署

> 对应文档：[`docs/08-devops-architecture/02-docker-deploy.md`](../../docs/08-devops-architecture/02-docker-deploy.md)  
> 状态：`已完成出题`  
> 建议用时：80～130 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 需安装 Docker。若无法安装：完成书面 Dockerfile/compose 设计题，并在笔记注明环境限制。
4. 建议目录：

```text
playground/08-devops-architecture/02-docker-deploy/
  app/main.py
  Dockerfile
  .dockerignore
  compose.yaml
  notes.md
```

5. Python 基础镜像可用 `python:3.12-slim`（与课程约定一致）；业务代码按 ≥3.11 编写。
6. **密钥不要写进镜像层**；用运行时 `-e` / compose `environment` / `env_file`。

---

## 热身题（建议先做）

### W1. 镜像 vs 容器（填空）

**要求**：用自己的话完成：镜像像 ____；容器像 ____。

**验收**：类比合理（模板/实例、类/对象等）。

---

### W2. 为何要有 `.dockerignore`

**要求**：列 3 类不该打进构建上下文的东西。

**验收**：如 `.git`、venv、`.env`、`__pycache__`。

---

### W3. 端口映射

**要求**：解释 `-p 8000:8000` 左右两侧各是谁的端口。

**验收**：左主机，右容器。

---

### W4. localhost 陷阱预告

**要求**：一句话：容器内访问 `localhost:5432` 常常连到谁？

**验收**：连到「该容器自己」，不是兄弟容器或宿主机（除非额外配置）。

---

## 基础题（必做）

### B1. 概念题（书面）

1. 对比镜像与容器各 **3 条**  
2. 解释：为何删容器不一定删镜像  

**验收**：点出「可重复创建实例」与「镜像是构建产物」。

---

### B2. Dockerfile + 最小 FastAPI health

为最小应用写：

- `app/main.py`：`GET /health` → `{"status":"ok"}`  
- `Dockerfile`  
- `.dockerignore`  

尝试：

```bash
docker build -t agent-api:dev .
docker run --rm -p 8000:8000 agent-api:dev
curl http://127.0.0.1:8000/health
```

若不能跑 Docker：把文件写全，并在 `notes.md` 说明限制。

**验收**：能跑则 `curl` 200；不能跑则文件完整可审阅。

---

### B3. 环境变量注入

用 `-e APP_API_KEY=...`（假值）注入，确认容器内应用能读到。

要求：

- 可临时打印「是否存在」或长度，**不要**把真实密钥打进日志仓库  
- 代码从 `os.environ` 读取  

**验收**：有注入命令 + 验证方式说明。

---

### B4. Compose 设计

写 `compose.yaml`：至少 `api` + `db`（Postgres）；Redis 可选。

标注：api 的 `DATABASE_URL` 主机名应写成 **服务名**（如 `db`），不是 `localhost`。

**验收**：compose 可读；网络主机名正确。

---

## 进阶题（建议至少做 1 题）

### A1. 多阶段构建草图

写一个两阶段 Dockerfile（可伪代码），说明最终镜像为何更小。

**验收**：build 阶段与 runtime 阶段分离；最终阶段不含编译器/缓存垃圾的大意。

---

### A2. 踩坑复盘（书面）

解释：容器内连 `localhost:5432` 为什么常常连错？正确应写什么（compose 场景）？

**验收**：服务名 / 用户定义网络。

---

## 挑战题（可选）

### C1. 数据卷

给 postgres 配 named volume；说明 `docker compose down -v` 的风险。

**验收**：知道 `-v` 会删卷导致数据没。

---

### C2. 健康检查

为 api 服务写 `HEALTHCHECK` 或 compose `healthcheck`，探测 `/health`。

**验收**：配置完整；说明失败时编排层可能做什么。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4
- [ ] **通过线**：B1～B4 完成（能跑则跑通）
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

### W1～W4 参考答案

- W1：镜像像类/只读模板；容器像实例/运行中的进程空间。  
- W2：`.git`、`.venv`、`.env`、测试产物、本地 IDE 目录。  
- W3：`-p 主机端口:容器端口`。  
- W4：容器自己的 loopback。

---

### B1 思路 + 参考答案

镜像：

1. 构建产物，分层存储  
2. 有标签与 ID  
3. 不写业务运行时状态（通常）  

容器：

1. 镜像 + 可写层 + 进程  
2. 可 start/stop  
3. 删容器不等于删镜像  

删容器只去掉实例与可写层；镜像仍在本地，可再次 `run`。

---

### B2 思路 + 参考答案

```python
# app/main.py
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```text
# requirements.txt
fastapi>=0.110
uvicorn[standard]>=0.27
```

```dockerignore
.git
.venv
__pycache__
*.pyc
.env
.env.*
playground
**/tests
```

```bash
docker build -t agent-api:dev .
docker run --rm -p 8000:8000 agent-api:dev
curl -sS http://127.0.0.1:8000/health
# {"status":"ok"}
```

---

### B3 思路 + 参考答案

```python
# 演示读取（勿打印密钥本身）
import os

def api_key_configured() -> bool:
    return bool(os.getenv("APP_API_KEY"))
```

```bash
docker run --rm -p 8000:8000 -e APP_API_KEY=fake-dev-key agent-api:dev
```

验证：临时加 `/debug/config` 返回 `{"api_key_set": true}`（练习后删掉该路由）。

---

### B4 思路 + 参考答案

```yaml
# compose.yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://agent:agent_dev_pwd@db:5432/agent_db
      APP_API_KEY: fake-dev-key
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: agent_dev_pwd
      POSTGRES_DB: agent_db
    ports:
      - "5432:5432"
```

注意：主机名是 **`db`**（服务名）。若 api 写 `localhost:5432`，会连到 api 容器自己。

---

### A1 思路 + 参考答案

```dockerfile
# 阶段 1：构建依赖（可含 build-essential）
FROM python:3.12-slim AS builder
WORKDIR /w
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# 阶段 2：运行期更瘦
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

最终镜像不携带编译缓存与无关工具链时通常更小、攻击面更小。

---

### A2 思路 + 参考答案

容器有独立网络命名空间：`localhost` 是自己。  
在 compose 默认网络中，应使用服务名 DNS，例如 `db:5432` / `redis:6379`。  
连宿主机服务才需要 host 网关之类特殊配置（本课了解即可）。

---

### C1 思路 + 参考答案

```yaml
services:
  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

`docker compose down -v` 会删除声明的 volume → **数据丢失**。日常停止用 `down`；清数据才加 `-v`。

---

### C2 思路 + 参考答案

```yaml
services:
  api:
    build: .
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 10s
      timeout: 3s
      retries: 3
```

或 Dockerfile `HEALTHCHECK`。编排可用健康状态决定是否切入流量 / 是否重启（取决于平台）。

---

## 附录：构建与运行检查清单

```bash
# 1) 上下文是否干净
cat .dockerignore

# 2) 构建
docker build -t agent-api:dev .

# 3) 跑起来
docker run --rm -p 8000:8000 -e APP_API_KEY=fake agent-api:dev

# 4) 探活
curl -sS http://127.0.0.1:8000/health

# 5) 看日志
docker logs <container_id>

# 6) 进入容器排查（必要时）
docker exec -it <container_id> sh
```

compose 版：

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f api
curl -sS http://127.0.0.1:8000/health
docker compose down          # 停服务
# docker compose down -v     # 危险：删卷
```

---

## 附录：镜像里不该有什么

1. `.env` 真密钥  
2. 本地 virtualenv  
3. `node_modules` / 大型数据集误 COPY  
4. 测试用私钥  
5. 完整 `.git` 历史  

反例（勿学）：

```dockerfile
ENV OPENAI_API_KEY=sk-xxxxxxxx   # 密钥进层，泄露风险极高
COPY . /app                      # 无 dockerignore 时极容易把垃圾打进去
```

正例思路：

```dockerfile
# 仅复制依赖清单与代码；密钥运行时注入
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
```

---

## 附录：自检

- [ ] 能分清镜像与容器  
- [ ] 能写最小 Dockerfile + `.dockerignore`  
- [ ] 能解释 compose 中 `db` 主机名  
- [ ] 知道 `down -v` 会删数据卷


---

## 附录：故障症状速查

| 症状 | 先查 |
|------|------|
| build 很慢/上下文巨大 | `.dockerignore` 是否排除 venv/.git |
| 容器启动秒退 | `docker logs`；CMD 模块路径是否 `app.main:app` |
| curl 连不上 | `-p` 映射；`--host 0.0.0.0` 是否漏了 |
| api 连不上 db | `DATABASE_URL` 主机名是否写成服务名 |
| 数据突然空了 | 是否误用 `compose down -v` |

**口头题**：镜像和容器差在哪？为什么密钥不能 `ENV` 进 Dockerfile？

### 最小 compose 验收命令

```bash
docker compose up --build -d
curl -sS http://127.0.0.1:8000/health
docker compose logs --tail=50 api
docker compose down
```
