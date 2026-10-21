# 模块 03-engineering：Python 工程化

> 状态：`四章正文与练习已全部完成` · 预计周期：1～2 周

## 模块目标

从「会写 Python」进入「会用 Python 做项目」。

## 为什么现在学

Agent 项目需要可维护结构、依赖管理、测试与日志。没有工程化，后面 FastAPI / RAG / Agent 很容易变成「只能在自己电脑上跑的演示脚本」。

## 章节目录

1. [项目结构](./01-project-structure.md) · [练习](../../exercises/03-engineering/01-project-structure.md)
2. [依赖与虚拟环境](./02-deps-venv.md) · [练习](../../exercises/03-engineering/02-deps-venv.md)
3. [测试（pytest）](./03-testing.md) · [练习](../../exercises/03-engineering/03-testing.md)
4. [Logging](./04-logging.md) · [练习](../../exercises/03-engineering/04-logging.md)

## 建议学习方式

1. 最好按顺序：先搭结构，再装依赖，再补测试与日志（每章保留知识地图骨架；知识点按「为什么 → 怎么写 → 跑一下 → 易错点」推进）
2. 练习尽量落在同一个 `my-agent/` 小项目上贯通，先按自己的理解做再对照
3. 只把「必掌握」吃透；uv/ruff/mock/CI 按兴趣加餐

## 模块自检

- [ ] 能从零搭一个可运行的 `app/` 项目骨架
- [ ] 能用虚拟环境安装依赖，并用环境变量管理密钥
- [ ] 能用 pytest 为纯逻辑写测试
- [ ] 能配置 logging，按字段记录工具/LLM 关键事件
- [ ] 清楚工程化如何服务后续 Agent 主线

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一模块：[高级特性与类型系统](../02-advanced-python/README.md)
- 下一模块：[计算机与服务端基础](../04-systems-basics/README.md)
