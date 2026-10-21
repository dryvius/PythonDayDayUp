# Docker 与部署

> 所属模块：`08-devops-architecture` · 部署、运维与软件架构  
> 状态：`已完成正文`  
> 建议学时：4～6 小时（有前端 Docker / 云主机经验可更快；镜像层、Compose 网络与多阶段建议动手踩一遍）  
> 对应练习：[`exercises/08-devops-architecture/02-docker-deploy.md`](../../exercises/08-devops-architecture/02-docker-deploy.md)

## 本章定位

- **模块目标**：具备把服务跑起来、拆清楚边界的能力。
- **本章角色**：理解镜像/容器；会写 Dockerfile；会用 Compose 编排 API + DB + Redis。
- **和 Agent**：本地一键起依赖；部署到服务器时环境一致——「我机器上能跑」变成「镜像里怎么跑就怎么跑」。
- **你的优势**：若用过前端的 `node` 镜像、Vite 多阶段构建，或云主机上装过 Postgres，概念可迁移；本章盯住 **Python/FastAPI 场景的层、网络名与密钥注入**，而不是背全部 Docker 子命令。

## 学习目标（学完应能做到）

1. 分清镜像与容器，能用 `pull` / `run` / `ps` / `logs` / `stop` / `rm` 完成最小生命周期。
2. 为 FastAPI 应用写可用 Dockerfile（约定示例基座：`python:3.12-slim`），并配合 `.dockerignore` 构建、运行、用环境变量注入密钥。
3. 用 Compose 编排多服务；写对服务间主机名与 `healthcheck` / `depends_on`。
4. 了解多阶段构建与环境隔离；K8s 仅扫盲（建立地图，不要求会写 YAML）。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 镜像/容器、Dockerfile、compose | 能本地编排跑通 |
| **建议掌握** | 多阶段构建、环境隔离 | 镜像更小更安全 |
| **了解即可** | K8s 扫盲 | 地图 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要 Docker？

Agent / 后端上线后，问题经常不是「代码写错」，而是「环境不一致」：

```text
本机 Python 3.12，服务器还是 3.10 → 语法/依赖炸
本机有 Postgres，同事没有 → 「连不上库」
本机装了系统级 lib，CI 没装 → 测试绿、部署红
LLM Key / DB URL 散落在 shell 历史里 → 难复现、易泄漏
```

Docker 把「代码 + 依赖 + 系统层」打成**可复制的运行单元**，让本地、CI、预发、生产用同一套镜像约定。

#### 本章要练的三种能力

1. **分清模板与实例**：镜像是只读模板，容器是运行中的实例
2. **打包应用**：Dockerfile 描述「怎么从源码变成可跑镜像」
3. **编排依赖**：Compose 把 API、Postgres、Redis 放进同一张网络，一键起停

可以先记一句：

> Docker 的核心价值：**把「能跑起来」从个人笔记本，变成可复制的制品与编排**。

#### 和「直接 pip + 本机 Postgres」差在哪？

| 方式 | 优点 | 缺点 |
| --- | --- | --- |
| 本机 venv + 本机 DB | 调试快、热重载方便 | 依赖本机脏环境；同事难复现 |
| Docker 单容器跑 API | 环境可复制 | 还要单独起 DB/Redis，网络要自己接 |
| Compose 多服务 | 一键起 API+DB+Redis，主机名稳定 | 要学一点 YAML 与网络概念 |

#### 前端 / 本机进程对照（先建立地图）

| 你熟悉的事 | Docker 大致对应 |
| --- | --- |
| `npm install` 后的 `node_modules` + 源码 | 镜像层里的依赖与代码 |
| `npm run start` 起一个进程 | `docker run` 起一个容器 |
| 同一份代码开多个终端跑多个实例 | 同一镜像起多个容器 |
| `localhost:5173` 访问 Vite | `-p 主机端口:容器端口` 映射后访问 |
| `docker-compose` 起前端 + mock API（若用过） | 本章 Compose：`api` + `db` + `redis` |

---

## 2. 必掌握：镜像 vs 容器

这一节会刻意写细——后面 Dockerfile、Compose、多阶段都建立在「镜像是模板、容器是实例」之上。

### 2.1 一句话分清

#### 为什么必须先分清？

混用这两个词时，排障会乱：

```text
「删了镜像怎么容器还在？」——其实你删的可能是容器
「为什么改了代码容器里还是旧的？」——你改的是主机文件，没重建镜像/没挂卷
「pull 了新版本，旧容器自动变新了吗？」——不会；旧容器仍挂着旧镜像层
```

#### 怎么理解

```text
镜像 image   = 只读模板（含代码 / 依赖 / 系统层）
容器 container = 镜像的运行实例（有进程、可写层、网络、端口）
```

关系直觉：

```text
镜像  ──docker run──►  容器 A（进程在跑）
  │
  └────docker run──►  容器 B（另一个实例，互不影响）
```

类比（帮助记忆，不必字面相等）：

| 类比 | 镜像 | 容器 |
| --- | --- | --- |
| 面向对象 | 类 | 对象实例 |
| 安装包 | 安装包 / 模板机 | 已开机的虚拟机里的一个进程环境 |
| Git | commit（只读快照感） | 基于某 commit checkout 后正在改的工作区（有可写层） |

#### 跑一下

先确认 Docker 可用，再走一遍最小生命周期（Postgres 作练习靶，不必先有业务代码）：

```bash
docker pull postgres:16
docker images
docker run --name pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16
docker ps
docker logs -f pg
# Ctrl+C 只停跟随，不停止容器
docker stop pg
docker rm pg
```

读命令含义：

| 命令 | 作用 |
| --- | --- |
| `pull` | 下载镜像到本机 |
| `images` | 列出本机镜像 |
| `run` | 基于镜像创建并启动容器（可加 `--name` / `-e` / `-p` / `-d`） |
| `ps` | 列出**运行中**容器（`ps -a` 含已退出） |
| `logs -f` | 跟随容器标准输出日志 |
| `stop` | 停止容器（镜像还在） |
| `rm` | 删除容器（镜像通常还在，除非你再 `rmi`） |

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为 `docker rm` 会删镜像 | 只删容器；镜像仍在 `docker images` 里 |
| `docker stop` 后以为镜像没了 | 镜像还在；可再 `docker start` 或重新 `run` |
| 把「容器里的改动」当成镜像永久内容 | 默认可写层随容器删而丢；要固化需 `commit`（教学不推荐）或写回 Dockerfile 重建 |
| 同一 `--name` 重复 `run` | 名字冲突；先 `rm` 旧容器或换名 |

#### 本机进程对照

| 本机 | Docker |
| --- | --- |
| 安装 Postgres 软件包 | `docker pull postgres:16` |
| 启动服务进程 | `docker run ... postgres:16` |
| `ps` / 任务管理器看进程 | `docker ps` |
| 看服务日志文件 | `docker logs` |
| 卸载软件 | `docker rmi`（删镜像）；停服务 ≈ `stop`/`rm` 容器 |

---

### 2.2 镜像层与「为何重建才生效」

#### 为什么要懂「层」？

Dockerfile 每一条 `RUN` / `COPY` 大致对应一层。构建会缓存未变的层——这既是加速点，也是「我改了文件怎么镜像还是旧的」的常见原因。

#### 怎么理解（心智图）

```text
python:3.12-slim          ← 基础层（官方）
  + apt/pip 装依赖        ← 依赖层（变依赖才重跑）
  + COPY 应用代码         ← 代码层（改代码常只需重跑后面）
  = 你的应用镜像
```

容器启动时：在镜像只读层之上加一层**可写层**。容器内 `apt install` / 改文件，默认只影响这个容器，不影响镜像模板。

#### 跑一下（观察，不必背输出）

```bash
docker images
# 注意 REPOSITORY / TAG / IMAGE ID / SIZE

docker run --rm -it python:3.12-slim bash -c "python -V && whoami && pwd"
# 退出后容器因 --rm 被删；镜像 python:3.12-slim 仍在
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 改了源码只 `docker restart` 旧容器 | 容器里仍是构建时 `COPY` 进去的旧代码（未挂卷时） |
| 以为 `pull` 会更新正在跑的容器 | 不会；要停旧容器，用新镜像再 `run` / `compose up` |
| 把巨大无关文件 `COPY` 进上下文 | 构建慢、镜像胖；用 `.dockerignore`（见下节） |

#### 对照：镜像 ID vs 容器 ID

```text
IMAGE ID     标识某份只读模板（同 tag 被覆盖后，旧 ID 可能变成 <none> 悬空）
CONTAINER ID 标识某次运行实例（每次 run 通常新 ID）
```

排障时先问：问题在**模板**（要重建镜像）还是在**实例**（看日志、环境变量、端口、卷）？

---

## 3. 必掌握：Dockerfile（FastAPI 示例）

这一节会刻意写细——能独立写出可构建、可访问、密钥不进层的 FastAPI 镜像，是 Compose 与部署的底座。  
约定基座：`python:3.12-slim`（与仓库 `docs/CONVENTIONS.md` 一致）。

### 3.1 最小可用 Dockerfile

#### 为什么需要 Dockerfile？

没有 Dockerfile，你只能口头说「先装 Python，再 pip install，再 uvicorn」。别人的机器步骤会漂。Dockerfile 把步骤写成**可重复构建脚本**，产出带 tag 的镜像。

#### 怎么写

假设项目大致是：

```text
.
├── app/
│   └── main.py          # FastAPI：app = FastAPI()
├── pyproject.toml
├── README.md
├── Dockerfile
└── .dockerignore
```

`app/main.py` 最小示意（教学用）：

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

Dockerfile：

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
# 因上面 COPY 了 ./app，uvicorn 靠工作目录 /app 即可找到包 app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

逐行直觉：

| 指令 | 作用 |
| --- | --- |
| `FROM python:3.12-slim` | 选瘦身官方 Python 基座 |
| `WORKDIR /app` | 后续命令的工作目录；也影响相对路径 |
| `COPY ...` | 把构建上下文中的文件放进镜像 |
| `RUN pip install ...` | 在构建期装依赖（打进镜像层） |
| `ENV PYTHONUNBUFFERED=1` | 让 `print`/日志尽快出到 `docker logs` |
| `EXPOSE 8000` | 文档性声明端口（真正映射靠 `run -p` / compose `ports`） |
| `CMD [...]` | 容器默认启动命令（exec 形式，信号更友好） |

#### 跑一下

在含 `Dockerfile` 的项目根目录：

```bash
docker build -t my-agent-api:dev .
docker run --rm -p 8000:8000 -e APP_API_KEY=dev my-agent-api:dev
```

另开终端：

```bash
curl -i http://127.0.0.1:8000/health
# 期望看到 200 与 {"status":"ok"}
```

构建与运行拆开记：

```text
build  →  得到镜像 my-agent-api:dev
run    →  基于该镜像起容器，并把主机 8000 映射到容器 8000
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `uvicorn` 只监听 `127.0.0.1` | 容器内环回；主机 `-p` 映射也访问不到 → 必须 `--host 0.0.0.0` |
| 密钥写成 `ENV APP_API_KEY=真实值` 并推仓库 | 密钥进镜像层与 Git 历史；应用 `-e` / compose `env_file` |
| 以为 `EXPOSE` 等于发布端口 | 不映射端口时主机仍访问不到 |
| `CMD` 写成 shell 字符串却忘了信号 | 优先 exec 形式 `CMD ["uvicorn", ...]` |
| 构建上下文指错目录 | `docker build` 最后的 `.` 是上下文根；Dockerfile 里的 `COPY` 相对它 |

#### 对照：本机启动 vs 容器启动

| 本机 | 容器 |
| --- | --- |
| `uvicorn app.main:app --reload --port 8000` | Dockerfile `CMD` + `docker run -p 8000:8000` |
| `export APP_API_KEY=dev` | `docker run -e APP_API_KEY=dev` |
| 看终端输出 | `docker logs -f <container>` |
| 改代码即时生效（`--reload`） | 默认需重建镜像；开发可再挂 volume（见 Compose） |

---

### 3.2 `.dockerignore`：别把垃圾打进上下文

#### 为什么需要？

`docker build` 会把上下文目录发给 Docker 引擎。若把 `.venv`、`.git`、`__pycache__`、本地数据卷拷进去：

1. 构建变慢
2. 镜像巨大且可能装错解释器/依赖
3. 偶发把密钥文件打进层

#### 怎么写

项目根 `.dockerignore` 最小示意：

```gitignore
.git
.venv
venv
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.env
.env.*
*.md
!README.md
.history
playground
```

按仓库实际情况增减；原则：**运行镜像不需要的，就不进上下文**。

#### 跑一下

加完 `.dockerignore` 后重新：

```bash
docker build -t my-agent-api:dev .
```

若之前镜像异常庞大，排除 `.venv` 后体积通常明显下降。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 镜像塞进 `.venv` | 巨大且可能是 Windows/mac 路径的环境，容器内不可用或错误 |
| 忽略了要用的 `app/` | 构建后 `ModuleNotFoundError` |
| 把 `.env` 打进镜像 | 密钥进层；应用运行时注入 |

#### 对照：`.gitignore` vs `.dockerignore`

| | `.gitignore` | `.dockerignore` |
| --- | --- | --- |
| 目的 | 不进 Git | 不进 build 上下文 / 镜像 |
| 典型排除 | `.venv`、`.env`、缓存 | 同样这些，再加测试缓存、无关文档等 |
| 是否互相替代 | 否 | 否——两边都要管 |

---

### 3.3 构建缓存与依赖/代码分层

#### 为什么要关心顺序？

若每次改一行 Python 都重装全部 pip 依赖，构建会又慢又吵。常见手法：先只复制依赖清单并安装，再复制源码——源码变时命中依赖层缓存。

#### 怎么写（比最小示例更「工程」一点）

当 `pyproject.toml` 可构建时：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 1) 先依赖清单（改代码不轻易让这一层失效）
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

# 2) 再业务代码
COPY app ./app

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

教学最小示意仍可用「直接 `pip install fastapi uvicorn`」；上线项目优先「清单驱动安装」，避免 Dockerfile 与 `pyproject` 两套依赖真相。

#### 跑一下

```bash
docker build -t my-agent-api:dev .
# 再改 app/main.py 后重建，观察：依赖安装层是否显示 CACHED
docker build -t my-agent-api:dev .
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 先 `COPY . .` 再 `pip install` | 任意文件变动都使依赖层缓存失效 |
| 依赖装在最终阶段却留了编译器 | 镜像胖（多阶段见第 5 节） |
| `--no-cache-dir` 忘了 | pip 缓存进层，体积变大（功能往往仍可用） |

#### 对照：前端多阶段印象

| 前端常见 | Python 对应直觉 |
| --- | --- |
| 先 `npm ci` 再 `COPY` 源码 | 先装依赖再 `COPY app` |
| 构建阶段 `npm run build`，运行阶段只拷 `dist` | 多阶段：构建期装编译依赖，运行期只留解释器+产物 |

---

### 3.4 运行时配置：环境变量与密钥

#### 为什么配置要进环境、不进镜像？

同一镜像应能跑在「本地 / 预发 / 生产」——变的是 **DB URL、API Key、日志级别**，不是三份 Dockerfile。这就是十二要素里「配置进环境」的朴素版。

#### 怎么写

构建期（Dockerfile）适合放**非秘密**默认值：

```dockerfile
ENV PYTHONUNBUFFERED=1
# 可选：ENV APP_ENV=production
```

运行期注入秘密与环境相关值：

```bash
docker run --rm -p 8000:8000 \
  -e APP_API_KEY=dev-key \
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/agent \
  my-agent-api:dev
```

应用内读取（示意）：

```python
import os

api_key = os.environ["APP_API_KEY"]  # 缺失即早失败，避免默默空串
```

#### 跑一下

```bash
docker run --rm -e APP_API_KEY=dev my-agent-api:dev \
  python -c "import os; print('set' if os.environ.get('APP_API_KEY') else 'missing')"
```

练习要求：确认「存在与否」，**不要**把真实密钥打印到日志或截图。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 密钥写死在 Dockerfile `ENV` 并推送 | 泄漏；镜像历史可被检查 |
| 本机 `export` 了就以为容器看得到 | 容器是独立进程环境；必须 `-e` / `env_file` / 编排注入 |
| 用默认空字符串吞掉缺失配置 | 运行时连错服务或鉴权失效，难排查 |

#### 对照：三种注入方式

| 方式 | 适用 |
| --- | --- |
| `docker run -e KEY=val` | 单容器快速试 |
| compose `environment:` / `env_file:` | 本地多服务 |
| 云平台「环境变量 / Secret」面板 | 预发/生产（概念同，界面不同） |

---

## 4. 必掌握：Compose 本地编排

这一节会刻意写细——Agent 本地开发几乎总是「API + DB（+ Redis）」一起起；Compose 解决的是**网络名、启动顺序、数据卷、一键起停**。

### 4.1 最小 `compose.yaml`：API + DB + Redis

#### 为什么需要 Compose？

只 `docker run` 一个 API 时，你还要：

```text
再 run 一个 postgres，记住容器 IP 或自己建网络
再 run 一个 redis
每次把 DATABASE_URL 指对主机名
API 抢在 DB ready 前启动 → 启动失败
```

Compose 用一份 YAML 声明多服务、默认加入同一网络，服务名即 DNS 名。

#### 怎么写

`compose.yaml`（或 `docker-compose.yml`）示意：

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

读 YAML 结构：

| 键 | 含义 |
| --- | --- |
| `services.api.build` | 用当前目录 Dockerfile 构建 |
| `ports` | `主机:容器` 端口映射 |
| `environment` | 注入到该服务容器 |
| `depends_on` + `condition` | 启动顺序与就绪条件 |
| `volumes`（服务内） | 把命名卷挂到 Postgres 数据目录 |
| 顶层 `volumes: pgdata` | 声明命名卷，数据可在容器删后仍保留 |

#### 跑一下

```bash
docker compose up --build
# 另开终端
curl -i http://127.0.0.1:8000/health
docker compose ps
docker compose logs -f api
# 停掉（默认不删命名卷）
docker compose down
```

常用补充：

```bash
docker compose down -v   # 连命名卷一起删 → 数据库数据没了，慎用
docker compose up -d     # 后台跑
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| API 连 `localhost:5432` | 容器内 localhost 是**自己**，不是 db 服务 → 应写主机名 `db` |
| 只写 `depends_on: db` 无 health | 默认只保证容器已启动，不保证 Postgres 可连 → API 抢连失败 |
| Redis/DB 端口映射以为「服务间必须」 | 服务间走内部网络即可；`ports` 主要为了主机调试 |
| `APP_API_KEY` 写进镜像而非 compose/`env_file` | 密钥进层；本地应用 compose 注入 |

#### 对照：主机名怎么写

| 从哪里连 | `DATABASE_URL` 主机部分 |
| --- | --- |
| 容器 `api` 连 Compose 里的 `db` | `db`（服务名） |
| 你笔记本上的 psql / GUI | `127.0.0.1`（因映射了 `5432:5432`） |
| 容器里误写 `localhost` | 指向 api 自己 → 连错 |

服务间主机名用 **服务名**（`db`、`redis`），不是 `localhost`。

---

### 4.2 网络、DNS 与「为什么叫 db」

#### 为什么服务名能当主机名？

Compose 项目默认创建桥接网络，并把服务名注册进内嵌 DNS。于是 `api` 容器里 `getaddrinfo("db")` 能解析到 db 容器 IP。

```text
[api 容器] --DNS: db--> [db 容器]:5432
[api 容器] --DNS: redis--> [redis 容器]:6379
[你的浏览器] --localhost:8000--> (端口映射) --> [api]:8000
```

#### 怎么写（心智，不必手写 network 块）

默认即可。若多个 compose 项目要互通，再学外部网络——本章先掌握默认网络足够。

URL 拼法提醒（与模块 07 一致）：

```text
postgresql+psycopg://用户:密码@db:5432/agent
                     │         │  │
                     │         │  └─ 容器内端口（镜像默认）
                     │         └──── 服务名
                     └────────────── 用户/库名与 db.environment 对齐
```

#### 跑一下

在 api 容器内探测（服务已 `up` 时）：

```bash
docker compose exec api python -c "import socket; print(socket.gethostbyname('db'))"
docker compose exec api python -c "import socket; print(socket.gethostbyname('redis'))"
```

能解析出 IP，就说明 DNS 正常（下一步才是业务驱动连接）。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把 compose 服务名写成 `postgres` 却在 URL 里写 `db` | 名字不一致就解析失败 |
| 混用旧容器 IP | IP 会变；应始终用服务名 |
| 防火墙只放行本机却怪 Docker | 先分清：浏览器走映射端口；容器间走内部 DNS |

#### 对照：前端代理直觉

| Vite `server.proxy` | Compose |
| --- | --- |
| 开发时把 `/api` 转到后端 | 浏览器只打到映射的 api 端口 |
| 前端容器里请求 `http://backend:3000` | api 里请求 `http://db:5432` 协议不同，但是「用服务名」同一思想 |

---

### 4.3 `healthcheck` 与启动顺序

#### 为什么 `depends_on` 不够？

Postgres 容器「进程已启动」≠「已接受连接」。API 若在初始化时立刻建连池，常见现象：第一次 `compose up` 失败，再重启又好了——典型竞态。

#### 怎么写

对 db：

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres -d agent"]
  interval: 5s
  timeout: 5s
  retries: 10
```

对 api：

```yaml
depends_on:
  db:
    condition: service_healthy
  redis:
    condition: service_started
```

含义：

- `service_healthy`：healthcheck 通过才继续
- `service_started`：容器已启动即可（Redis 通常足够；若你有严格就绪需求可再加 healthcheck）

#### 跑一下

```bash
docker compose up --build
docker compose ps
# db 的 STATUS 应出现 healthy（视 Docker 版本显示略有差异）
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| healthcheck 用户/库名与 `POSTGRES_*` 不一致 | 永远 unhealthy，api 一直等 |
| 应用自己不做重试，只靠 compose | 运行中 DB 短暂不可用仍可能炸；compose 只解决**启动序** |
| 把 `condition` 写在不支持的旧 compose 上 | 升级 Docker Compose v2；或退化为应用层重试 |

#### 对照：应用层重试

| 层 | 解决什么 |
| --- | --- |
| Compose health + depends_on | 冷启动时别抢连 |
| 应用连接池 / 重试 | 运行中闪断、滚动发布 |

教学环境先把 compose 就绪条件写对；生产还要应用侧韧性（后续架构/工程章会再遇到）。

---

### 4.4 数据卷：别把数据库当一次性容器

#### 为什么要挂卷？

Postgres 数据默认写在容器可写层里。`docker compose down` 删容器后，**未挂卷则数据可能没了**。命名卷把数据放到 Docker 管理的持久位置。

#### 怎么写

```yaml
db:
  volumes:
    - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

#### 跑一下

```bash
# 写入一些数据（用你的迁移/SQL 工具）后：
docker compose down
docker compose up -d
# 数据应还在

# 危险对照（勿在有用数据上随手试）：
# docker compose down -v
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 忘记挂卷 | 一 `down`/重建，库空了 |
| 随手 `down -v` | 命名卷删除 → 丢库 |
| 把主机机密目录随便 `-v` 进容器且权限过宽 | 泄漏面变大；密钥文件权限见 Linux 章 |

#### 对照：三种挂载直觉

| 类型 | 直觉 | 本章用法 |
| --- | --- | --- |
| 命名卷 named volume | Docker 管生命周期 | `pgdata` 给 Postgres |
| 绑定挂载 bind mount | 映射主机目录 | 开发时挂源码热重载（可选） |
| 匿名卷 | 易乱 | 教学少用 |

---

### 4.5 开发期可选：源码挂载与热重载

#### 为什么有时还要挂源码？

每次改一行都 `build` 太慢。开发可把主机 `./app` 挂进容器，并让 uvicorn `--reload`（**仅开发**；生产镜像仍用 `COPY` 固化）。

#### 怎么写（可选片段）

```yaml
api:
  build: .
  command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
  volumes:
    - ./app:/app/app
  # environment / depends_on 同前
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 生产也开 `--reload` | 多余监视、行为与产物不一致 |
| 挂载把容器内已安装包路径盖住 | 依赖「消失」；只挂业务目录 |
| 以为挂载就不需要镜像里的依赖 | 依赖仍要在镜像（或另一层）装好 |

#### 对照：前端 dev server

| Vite `--host` 热更新 | uvicorn `--reload` + bind mount |
| --- | --- |
| 改文件即刷新 | 改 `app/` 即重载 |
| 生产用 build 产物 | 生产用无 reload 的 `CMD` |

---

## 5. 建议掌握：多阶段构建与隔离

### 5.1 多阶段构建

#### 为什么需要多阶段？

有些 Python 包需要编译器、头文件才能 `pip install`。若编译工具留在最终镜像：

```text
体积大
攻击面大（多余工具）
与「运行只需解释器 + 站点包」的目标不符
```

多阶段：构建阶段装编译依赖并安装包；运行阶段用干净的 `python:3.12-slim`，只拷贝已安装产物（或轮子/虚拟环境）。

#### 怎么写（示意）

```dockerfile
# ===== 阶段 1：构建 =====
FROM python:3.12-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir --prefix=/install .

# ===== 阶段 2：运行 =====
FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app ./app

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

读结构：

```text
AS builder     给阶段命名
COPY --from=   只把需要的文件拷到最终镜像
最终 FROM      重新开始，不自动继承 builder 的编译器层
```

练习 A1 可先写「伪代码两阶段」，说清：最终镜像为何没有 `build-essential`。

#### 跑一下

```bash
docker build -t my-agent-api:prod .
docker images my-agent-api
# 与单阶段镜像比 SIZE（具体数值随依赖变化）
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 最终阶段忘了 `COPY` 应用代码或站点包 | 容器起不来 / `ModuleNotFoundError` |
| 构建阶段用 3.12、运行阶段用 3.11 | ABI/语法不一致风险；两阶段 Python 版本应对齐 |
| 为「小」而用过于冷门的 base | 排障成本上升；教学/项目优先官方 `slim` |

#### 对照：前端 Node 多阶段

| 前端 | Python |
| --- | --- |
| stage1: `npm ci && npm run build` | stage1: 编译依赖 + `pip install` |
| stage2: nginx 只拷 `dist` | stage2: slim 只拷已安装包 + `app` |
| 最终无 node_modules 源码树（视方案） | 最终无 `build-essential` |

---

### 5.2 环境隔离：同一镜像，不同配置

#### 为什么强调「同一镜像」？

若「生产专用 Dockerfile」与「本地 Dockerfile」长期分叉，会出现：本地绿、生产红，且难以复现。更稳的做法：

```text
同一镜像制品（或同一构建流水线产物）
× 不同环境变量 / 密钥 / 外部托管 DB
= 不同环境
```

#### 怎么写（做法表）

| 环境 | 做法 |
|------|------|
| 本地 | compose + `.env`（`.env` 不进 Git；示例用 `.env.example`） |
| 预发/生产 | 不同 tag 或同一 tag + 不同密钥、不同 DB；平台注入 Secret |
| 镜像 tag | `my-agent-api:dev` / `:staging` / `:git-sha` —— 可追溯 |

`.env` 示例（勿提交真实值）：

```env
APP_API_KEY=dev-key
POSTGRES_PASSWORD=postgres
```

compose 可：

```yaml
api:
  env_file:
    - .env
  environment:
    DATABASE_URL: postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@db:5432/agent
```

（变量插值细节以你本机 Compose 版本文档为准；原则是**秘密不进镜像层、不进 Git**。）

#### 跑一下

```bash
# 用不同 APP_API_KEY 起两次（或改 .env 后 compose up）
# 确认应用读到的是运行时注入，而不是构建进镜像的值
docker compose up --build
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 为每个环境维护一份完全不同的 Dockerfile | 漂移；缺陷只在某一环境出现 |
| 把生产 `.env` 提交到仓库 | 密钥泄漏 |
| tag 永远 `:latest` 且无记录 | 回滚困难；至少在预发/生产用不可变 tag（git sha） |

#### 对照：十二要素（只记与本章相关的）

| 原则（简化） | 本章落地 |
| --- | --- |
| 配置进环境 | `-e` / `env_file` / 平台 Secret |
| 后端服务当附加资源 | DB/Redis 是依赖，用 URL 指向 |
| 尽量无状态进程 | 会话/文件落 DB 或对象存储，不落容器可写层 |

同一镜像，不同配置；**十二要素**思想：配置进环境，不进代码。

---

## 6. 了解即可：K8s 扫盲

#### 为什么现在只扫盲？

个人项目与小团队用 Compose（或单机 Docker）通常足够。K8s 解决的是**多节点、自愈、滚动发布、服务发现与 Ingress 规模化**——概念重、YAML 面大。本章目标是：听到名词时知道它在地图的哪一格，而不是会写生产级集群配置。

#### 怎么建立地图（名词对照）

| Compose / Docker 直觉 | K8s 大致对应 |
| --- | --- |
| 一个容器 | 容器（Container）；常落在 Pod 里 |
| 一组紧密耦合的容器 | **Pod**（最小调度单元） |
| `docker run` 多个副本 | **Deployment** 声明副本数与滚动更新 |
| 服务名 DNS（`db`、`api`） | **Service** 稳定虚拟 IP / DNS |
| `ports` + 反向代理 | **Ingress**（HTTP 入口规则） |
| 本机卷 / 命名卷 | Volume / PVC（持久卷声明） |
| `docker compose up` | 集群调度器把 Pod 放到某节点 |

极简心智图：

```text
Deployment ──创建/维持──► Pod(s) ──内含──► Container(s)
                ▲
Service ──稳定访问──┘
Ingress ──从集群外 HTTP 引入──► Service
```

#### 跑一下（本章不做）

不必在本机起集群。若以后用云厂商「容器服务」，控制台创建的往往就是 Deployment + Service + Ingress 的托管版——概念可对上表。

#### 易错点（认知向）

| 错法 | 会发生什么 |
| --- | --- |
| 项目第一天就上 K8s | 运维面压过业务；先 Compose 跑稳 |
| 以为 K8s 替代了 Dockerfile | 镜像仍要先有；K8s 编排的是**已构建镜像** |
| 把 Pod IP 写死进配置 | Pod 重建 IP 变；应通过 Service DNS |

#### 对照：你现在该停在哪

| 阶段 | 够用工具 |
| --- | --- |
| 本地开发 Agent API + DB | Compose |
| 单机/单台云主机 | Compose 或 systemd + Docker |
| 多副本、多节点、复杂发布 | 再学 K8s / 云托管编排 |

个人项目 compose 足够；入职后再学 K8s 不迟。

---

## 7. 常见坑

1. **应用连 `localhost:5432`**（在容器里 localhost 是自己）→ 用服务名 `db`
2. **把密钥 `ENV` 写死在 Dockerfile 并推送仓库** → 运行时 `-e` / `env_file` / Secret
3. **镜像塞进 `.venv`** → 巨大且错误；用 `.dockerignore`，在镜像内 `pip install`
4. **数据卷忘记挂载，`compose down -v` 丢库** → 命名卷 + 慎用 `-v`
5. **uvicorn 未监听 `0.0.0.0`** → 主机端口映射无效
6. **`depends_on` 无 health，API 抢连 Postgres** → `healthcheck` + `condition: service_healthy`
7. **改了代码只 restart 旧容器** → 未挂卷时需 `--build` 重建；或开发挂载源码
8. **服务名与 URL 主机名不一致** → `db` 就是 `db`，两边对齐

---

## 8. 练习指引

按 [`exercises/08-devops-architecture/02-docker-deploy.md`](../../exercises/08-devops-architecture/02-docker-deploy.md) 完成：

| 题号 | 对应本节 | 建议 |
| --- | --- | --- |
| B1 镜像 vs 容器 | §2 | 书面对比即可 |
| B2 Dockerfile + `.dockerignore` | §3 | 能 `build`/`run`，`curl /health` |
| B3 `-e` 注入 | §3.4 | 只验证存在，不打印密钥 |
| B4 Compose API+DB | §4 | 标明 `DATABASE_URL` 主机名；Redis 可选 |
| A1 多阶段草图 | §5.1 | 伪代码说明为何更小 |
| A2 localhost 踩坑 | §4.2 | 书面复盘 |
| C1 命名卷 | §4.4 | 说明 `down -v` 风险 |

无法安装 Docker 时：完成书面 Dockerfile/compose 设计题，并注明环境限制（与练习页一致）。

---

## 9. 小结与下一站

### 自检

- [ ] 能解释镜像/容器差异，并说出删容器不必删镜像
- [ ] 能写并构建简单 Dockerfile（`python:3.12-slim` + FastAPI/uvicorn，监听 `0.0.0.0`）
- [ ] 会用 `.dockerignore`，密钥不进镜像层
- [ ] 能读懂 compose 多服务与网络名；`db`/`redis` 作主机名；healthcheck 避免抢连
- [ ] （建议）能口述多阶段为何更小；同一镜像不同配置
- [ ] （了解）知道 Pod / Service / Deployment / Ingress 在地图上的位置

### 可以带走的句子

> 镜像是只读模板，容器是运行实例；Compose 用服务名把 API 与 DB 接进同一网络；配置进环境，秘密别打进层。

### 下一章

[`03-software-architecture.md`](./03-software-architecture.md) —— 分层与边界，避免 Agent 变成大泥球。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Linux 基础](./01-linux-basics.md)
- 下一章：[软件架构基础](./03-software-architecture.md)
