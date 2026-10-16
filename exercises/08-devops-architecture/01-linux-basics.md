# 练习：Linux 基础

> 对应文档：[`docs/08-devops-architecture/01-linux-basics.md`](../../docs/08-devops-architecture/01-linux-basics.md)  
> 状态：`已完成出题` · 建议用时：45～80 分钟

可用 WSL / 远程 Linux / 云主机。Windows 原生环境请尽量用 WSL 完成命令题。

---

## 基础题（必做）

### B1. 命令速通

在练习目录创建树 `demo/a/b`，写入文件，用 `grep` 搜关键字，用 `tail` 查看；把命令清单写入 `b1_commands.md`。

### B2. 进程与端口

启动任意本地服务，或用 `python -m http.server 8765`，练习：`ps/grep`、`ss`/`netstat`、`curl` 健康检查；记录输出摘要。

### B3. 权限

创建假 `.env`，`chmod 600`，用 `ls -l` 验证；书面说明为何密钥文件不要 `777`。

### B4. 环境变量作用域

在一个 shell `export DEMO_VAR=1`，另开一个新 shell 观察是否可见；写结论。

---

## 进阶题（建议）

### A1. 排障剧本

假设「502 + 端口没人听」，写你的 5 步检查顺序。

### A2. systemd 地图（书面）

解释 `enable` / `start` / `status` / `journalctl -u` 各干什么。

---

## 挑战题（可选）

### C1. 日志轮转认知

说明若不轮转，长期 `INFO` 刷盘可能造成什么后果；关键词有哪些（logrotate 等）。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
