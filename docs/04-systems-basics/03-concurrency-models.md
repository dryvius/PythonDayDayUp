# 并发模型

> 所属模块：`04-systems-basics` · 计算机与服务端基础  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/04-systems-basics/03-concurrency-models.md`](../../exercises/04-systems-basics/03-concurrency-models.md)

## 本章定位

- **本章角色**：在写 asyncio 专章前，先建立「并发选项地图」，避免盲选。
- **和 Agent**：要同时等多个工具、多个嵌入请求、多个 LLM 调用——必须懂并发。

## 学习目标

1. 分清并行与并发。
2. 对比多线程 / 多进程 / 异步的适用场景。
3. 建立 Python GIL 直觉（知道它限制什么、不限制什么）。
4. 能对具体任务选出合理模型。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 并行 vs 并发、三种模型对比、GIL 直觉 | 能选型 |
| **建议掌握** | 何时选哪种 | 能讲清理由 |
| **了解即可** | 无锁结构 | 扫盲 |

---

## 1. 为什么要学

同步写法：

```text
search()   等 800ms
browse()   等 1200ms
embed()    等 500ms
总计 ≈ 2.5s
```

并发写法（I/O 重叠）：

```text
search + browse + embed 同时等
总计 ≈ 1.2s（约等于最慢那个）
```

Agent 延迟体验往往取决于你会不会重叠 I/O。

---

## 2. 必掌握：并行 vs 并发

| 概念 | 含义 | 例子 |
|------|------|------|
| **并发 concurrency** | 同一时段交替推进多个任务 | 单核上边等网络边切换任务 |
| **并行 parallelism** | 同一时刻真正一起执行 | 多核同时算 |

一句话：

> 并发是结构问题；并行是硬件同时执行问题。

异步编程首先解决的是**高并发 I/O**，不一定等于多核并行算力。

---

## 3. 必掌握：三种模型对比

### 3.1 多线程（threading）

- 同进程共享内存
- 适合：**阻塞 I/O** 等待（在等的时候释放 GIL，其它线程可跑）
- 风险：竞态、加锁复杂
- CPU 密集：受 GIL 限制，加速有限

### 3.2 多进程（multiprocessing）

- 多解释器进程，**可绕过 GIL** 做 CPU 并行
- 代价：内存更大、进程间通信更重
- 适合：解析大量文本、CPU 重计算（Agent 主路径较少，数据预处理常见）

### 3.3 异步（asyncio）

- 单线程（通常）+ 事件循环 + 协作式多任务
- 适合：**大量网络 I/O**、高并发连接
- 要求：调用链基本异步化（`async/await`）
- Agent / FastAPI / httpx AsyncClient 主战场

### 3.4 对照表

| 需求 | 更优选项 |
|------|----------|
| 同时等很多 HTTP | asyncio |
| 调用阻塞库又不想改 | 线程池 |
| 压榨多核 CPU | 多进程 / 本地扩展 |
| 简单脚本偶发并发 | `concurrent.futures` |

---

## 4. 必掌握：GIL 直觉

CPython 有 **Global Interpreter Lock**：同一时刻通常只有一个线程在执行 Python 字节码。

含义：

- **CPU 密集多线程 ≠ 线性加速**
- **I/O 等待时**线程常释放 GIL，多线程仍有用
- 多进程 / 别的运行时 / native 扩展是另一条路

不要把 GIL 理解成“Python 不能并发”——它限制的是**并行执行 Python 字节码**。

了解即可：CPython 3.13+ 有实验性 free-threaded（无 GIL）构建，生态与默认安装仍在演进；**本教程默认仍按「有 GIL」心智**选型。

---

## 5. 建议掌握：如何选型（Agent 清单）

```text
1) 主要是等 LLM/HTTP？ → asyncio（下一模块细学）
2) 某库只有同步客户端？ → 线程池包一层，或找异步替代
3) 大量 CPU 预处理？ → 多进程或预处理离线做完
4) 需要共享复杂可变状态？ → 先避免；再用队列传消息，少共享内存
```

经验法则：

> **默认异步 I/O；CPU 重活单独拿出去；少在热路径上裸加锁共享状态。**

---

## 6. 了解即可：无锁结构

无锁队列、CS 算法、原子操作——高并发中间件才会深挖。  
应用层优先用队列与不可变消息传递。

---

## 7. 最小代码直觉（同步对比）

```python
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def fake_io(name: str, sec: float) -> str:
    time.sleep(sec)  # 假装网络
    return name


def sequential() -> list[str]:
    return [fake_io("a", 0.2), fake_io("b", 0.2)]


def threaded() -> list[str]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(fake_io, n, 0.2) for n in ("a", "b")]
        # as_completed：按完成顺序；不要假设 == ["a", "b"]
        return [f.result() for f in as_completed(futs)]


def threaded_in_order() -> list[str]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(fake_io, n, 0.2) for n in ("a", "b")]
        return [f.result() for f in futs]  # 按提交顺序等结果
```

自己测耗时：线程版应明显更快（都在 sleep）。断言结果时用「集合相等」或 `threaded_in_order()`。

---

## 8. 常见坑

1. 在异步里调用长时间阻塞函数，卡住事件循环
2. 多线程改同一 list/dict 不加保护
3. 为了“快”无脑上多进程，调试成本爆炸
4. 把并行当银弹：任务本身是串行依赖就重叠不了

---

## 9. 练习指引

[`exercises/04-systems-basics/03-concurrency-models.md`](../../exercises/04-systems-basics/03-concurrency-models.md)

---

## 10. 小结与下一站

### 自检

- [ ] 能区分并发/并行
- [ ] 能说明 GIL 对线程 CPU 任务的影响
- [ ] 能给 Agent I/O 场景选出异步/线程池

### 下一章

[`04-dsa-essentials.md`](./04-dsa-essentials.md) —— 数据结构与算法精要（工程选型向，不走刷题主线）。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[网络与 HTTP](./02-network-http.md)
- 下一章：[数据结构与算法精要](./04-dsa-essentials.md)
