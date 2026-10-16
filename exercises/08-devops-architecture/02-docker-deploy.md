# 练习：Docker 与部署

> 对应文档：[`docs/08-devops-architecture/02-docker-deploy.md`](../../docs/08-devops-architecture/02-docker-deploy.md)  
> 状态：`已完成出题` · 建议用时：70～120 分钟

需安装 Docker。若无法安装：完成书面 Dockerfile/compose 设计题，并注明环境限制。

---

## 基础题（必做）

### B1. 概念题

对比镜像与容器各 3 条；解释为何删容器不一定删镜像。

### B2. Dockerfile

为你的最小 FastAPI `health` 应用写 Dockerfile + `.dockerignore`；尝试 `build` 与 `run`，`curl /health`。

### B3. 环境变量

用 `-e APP_API_KEY=...` 注入，确认容器内应用能读到（可临时打印是否存在而非打印值）。

### B4. Compose 设计

写 `compose.yaml`：`api` + `db(postgres)`（redis 可选）；标注 api 应如何写 `DATABASE_URL` 主机名。

---

## 进阶题（建议）

### A1. 多阶段构建草图

写一个两阶段 Dockerfile 伪代码，说明最终镜像为何更小。

### A2. 踩坑复盘（书面）

解释：容器内连 `localhost:5432` 为什么常常连错；正确应写什么。

---

## 挑战题（可选）

### C1. 数据卷

给 postgres 配 named volume；说明 `down -v` 的风险。

---

## 验收标准

- [ ] B1～B4 完成（能跑则跑通）
- [ ] （建议）A1 或 A2
