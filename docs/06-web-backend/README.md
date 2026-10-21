# 模块 06-web-backend：Web 后端

> 状态：`三章正文与练习已全部完成` · 预计周期：2 周

## 模块目标

能独立搭建并理解后端 API 服务。

## 为什么现在学

Agent 常以服务形式对外提供能力，也要调用其他 API。FastAPI + Pydantic 是当前最主流的 Python Agent 服务化组合之一。

## 章节目录

1. [Web 框架原理](./01-web-framework-principles.md) · [练习](../../exercises/06-web-backend/01-web-framework-principles.md)
2. [FastAPI + Pydantic](./02-fastapi-pydantic.md) · [练习](../../exercises/06-web-backend/02-fastapi-pydantic.md)
3. [认证与授权](./03-auth.md) · [练习](../../exercises/06-web-backend/03-auth.md)

## 建议学习方式

1. 先原理后动手：生命周期清楚再写路由（每章保留知识地图骨架；知识点按「为什么 → 怎么写 → 跑一下 → 易错点」推进）
2. 第二章请真实跑起 uvicorn，用 `/docs` 调试
3. 第三章把 API Key 加到你的 `/v1/agent/run` 上，形成最小可分享服务雏形
4. 可与总览中的 Project 2（FastAPI Todo）结合；先自己写再对照文档

## 模块自检

- [ ] 能描述请求生命周期与中间件职责
- [ ] 能独立写出带 Pydantic 校验的 API
- [ ] 能用 Depends 做配置与 API Key 鉴权
- [ ] 能区分认证/授权与 401/403
- [ ] 清楚异步路由中不能阻塞

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一模块：[Python 异步编程](../05-async-python/README.md)
- 下一模块：[数据库与数据持久化](../07-data-persistence/README.md)
