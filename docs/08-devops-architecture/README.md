# 模块 08-devops-architecture：部署、运维与软件架构

> 状态：`三章正文与练习已全部完成` · 预计周期：1～2 周

## 模块目标

具备把服务跑起来、拆清楚边界的能力。

## 为什么现在学

生产级 Agent 不只是脚本，还要部署、隔离与可演进架构。本模块把「能在笔记本跑」推进到「能在服务器以一致方式运行」。

## 章节目录

1. [Linux 基础](./01-linux-basics.md) · [练习](../../exercises/08-devops-architecture/01-linux-basics.md)
2. [Docker 与部署](./02-docker-deploy.md) · [练习](../../exercises/08-devops-architecture/02-docker-deploy.md)
3. [软件架构基础](./03-software-architecture.md) · [练习](../../exercises/08-devops-architecture/03-software-architecture.md)

## 建议学习方式

1. Linux 命令尽量上手；Windows 可用 WSL
2. Docker 章节以 compose 编排 API+DB 为目标
3. 架构章重在依赖方向，不必一上来上完整整洁架构
4. 与模块 03/06/07 的项目骨架对照着改

## 模块自检

- [ ] 能查进程/端口/日志并做基础排障
- [ ] 能写 Dockerfile 并用 compose 理解多服务网络
- [ ] 能画出 Agent 分层并说明密钥管理
- [ ] 认同「模块化单体优先，按需拆分」

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一模块：[数据库与数据持久化](../07-data-persistence/README.md)
- 下一模块：[AI / LLM 基础](../09-ai-llm/README.md)
