# 练习：Linux 基础

> 对应文档：[`docs/08-devops-architecture/01-linux-basics.md`](../../docs/08-devops-architecture/01-linux-basics.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 可用 WSL / 远程 Linux / 云主机。Windows 原生环境请尽量用 **WSL** 完成命令题。
4. 建议目录（在 Linux/WSL 家目录或仓库内）：

```text
playground/08-devops-architecture/01-linux-basics/
  b1_commands.md
  b2_notes.md
  fake.env
  notes.md
```

5. 先自己敲命令再写笔记；文末有参考命令清单。
6. 不要在仓库提交真实密钥。

---

## 热身题（建议先做）

### W1. 你在哪？

**要求**：用命令打印当前工作目录与当前用户。

**验收**：用到 `pwd` 与 `whoami`（或等价）。

---

### W2. 列目录

**要求**：列出当前目录详情（含隐藏文件）。

**验收**：`ls -la` 或等价。

---

### W3. 管道直觉

**要求**：用一句话说明 `cmd1 | cmd2` 在干什么。

**验收**：stdout 接到下一命令 stdin。

---

### W4. 退出码

**要求**：运行一个成功命令与一个失败命令，观察 `echo $?`。

**验收**：知道 0 通常表示成功。

---

## 基础题（必做）

### B1. 命令速通

在练习目录创建树 `demo/a/b`，写入文件，用 `grep` 搜关键字，用 `tail` 查看。  
把**实际使用的命令清单**写入 `b1_commands.md`。

最低要求：

1. `mkdir -p`  
2. 写入含关键字的文件（`echo`/`printf`/`cat` heredoc）  
3. `grep`  
4. `tail`  

**验收**：笔记中命令可复现；能搜到你写的关键字。

---

### B2. 进程与端口

启动任意本地服务，推荐：

```bash
python -m http.server 8765
```

练习并记录摘要到 `b2_notes.md`：

1. 用 `ps` + `grep`（或 `pgrep`）找到进程  
2. 用 `ss` 或 `netstat` 看端口监听  
3. 用 `curl` 做一次健康/首页检查  

**验收**：笔记含命令与关键输出摘要（可打码）。

---

### B3. 权限

1. 创建假 `.env`（内容用假密钥）  
2. `chmod 600`  
3. `ls -l` 验证  
4. 书面说明：为何密钥文件不要 `777`

**验收**：权限位显示为 `-rw-------` 或等价；理由提到「他人可读」。

---

### B4. 环境变量作用域

1. 在一个 shell：`export DEMO_VAR=1`  
2. **另开一个新 shell** 观察是否可见  
3. 写结论到 `notes.md`

**验收**：结论正确——`export` 影响当前进程及其子进程，不自动进无关新会话（除非写入 profile）。

---

## 进阶题（建议至少做 1 题）

### A1. 排障剧本

假设线上现象：**502 + 端口没人听**。写你的 **5 步**检查顺序。

**验收**：从「进程是否在 / 端口是否听 / 代理是否指错 / 日志 / 最近发布」等展开，顺序合理。

---

### A2. systemd 地图（书面）

解释下列各干什么：

- `systemctl enable`
- `systemctl start`
- `systemctl status`
- `journalctl -u <service>`

**验收**：enable ≠ start；日志用 journalctl。

---

## 挑战题（可选）

### C1. 日志轮转认知（书面）

说明若不轮转，长期 `INFO` 刷盘可能造成什么后果；关键词有哪些（`logrotate`、磁盘打满、inode 等）。

**验收**：至少提到磁盘耗尽与排障手段之一。

---

### C2. 一页「发布后检查清单」

为自己的 Agent API 列发布后 6 条检查（health、日志、端口、依赖 DB、错误率、回滚出口）。

**验收**：可执行、非空话。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4
- [ ] **通过线**：B1～B4 完成并有笔记
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

### W1～W4 参考答案

```bash
pwd
whoami
ls -la
# 管道：左命令标准输出作为右命令标准输入
true; echo $?    # 0
false; echo $?   # 非 0
```

---

### B1 思路 + 参考答案

**参考命令清单（`b1_commands.md`）**

```bash
cd playground/08-devops-architecture/01-linux-basics
mkdir -p demo/a/b
printf 'agent status=ok\nhello rag\n' > demo/a/b/app.log
grep -n "rag" demo/a/b/app.log
tail -n 2 demo/a/b/app.log
```

---

### B2 思路 + 参考答案

```bash
# 终端 1
python -m http.server 8765

# 终端 2
ps aux | grep -i '[h]ttp.server'
ss -ltnp | grep 8765
# 或: netstat -ltnp | grep 8765
curl -sS -D- http://127.0.0.1:8765/ -o /dev/null
```

笔记写：PID、监听地址、`curl` 状态码（常 200）。

---

### B3 思路 + 参考答案

```bash
printf 'APP_API_KEY=fake-not-real\n' > fake.env
chmod 600 fake.env
ls -l fake.env
# 期望：-rw------- 1 you you ... fake.env
```

书面：`777` 让「其它用户」也可读写，密钥等同公开；最小权限原则下私钥/令牌文件常用 `600`。

---

### B4 思路 + 参考答案

```bash
# shell A
export DEMO_VAR=1
echo "$DEMO_VAR"   # 1

# shell B（新开）
echo "${DEMO_VAR-unset}"  # 通常 unset
```

结论：环境变量不会「感染」所有已存在终端；新会话需重新 export 或写入 `~/.bashrc` 等（生产更常用 systemd/容器环境注入）。

---

### A1 思路 + 参考答案

五步示例：

1. 确认现象范围：仅该服务 502 还是全局  
2. `systemctl status` / 容器 `ps`：进程在不在  
3. `ss -ltnp`：业务端口是否监听；是否只绑了 `127.0.0.1`  
4. 查反向代理 upstream 配置是否指向旧端口/旧 socket  
5. `journalctl -u ... -n 200` / 应用日志看崩溃与启动失败；必要时回滚  

---

### A2 思路 + 参考答案

- `enable`：开机自启（改 symlink），不保证现在已运行  
- `start`：立即启动  
- `status`：当前是否 active、最近日志摘要  
- `journalctl -u`：对该 unit 的日志检索  

---

### C1 思路 + 参考答案

后果：根分区打满 → 写入失败、数据库/容器异常、SSH 都可能受影响。  
关键词：`logrotate`、按大小/按天切割、压缩、保留份数、监控磁盘与 inode、集中式日志。

---

### C2 思路 + 参考答案

1. `curl /health` 200  
2. 关键探针打到正确实例  
3. 错误日志无新增刷屏  
4. DB/Redis 连通性  
5. 核心 API 一次烟雾调用  
6. 确认回滚命令/上一版本镜像可用

---

## 附录：常用命令速查（可抄到笔记）

### 文件与文本

```bash
pwd
ls -la
mkdir -p path/to/dir
cp src dst
mv old new
rm -i file          # 练习环境慎用 rm -rf
cat file
less file
head -n 20 file
tail -n 50 file
tail -f file        # 跟踪日志
grep -R "TRACE_ID" -n .
```

### 进程与端口

```bash
ps aux | grep uvicorn
pgrep -a uvicorn
ss -ltnp
curl -v http://127.0.0.1:8000/health
kill -15 <pid>      # 先优雅退出
```

### 权限与环境

```bash
chmod 600 fake.env
ls -l fake.env
export APP_ENV=dev
env | grep APP_
unset DEMO_VAR
```

### 磁盘与日志（了解）

```bash
df -h
du -sh /var/log/*
# 日志打满前先定位最大文件，再谈删/轮转；生产优先 logrotate
```

---

## 附录：502 排障决策树（扩展 A1）

```text
收到 502
  ├─ 代理能否解析 upstream 主机名？
  │    └─ DNS/compose 服务名写错 → 先修配置
  ├─ upstream 端口有人听吗？（ss）
  │    └─ 没有 → 看进程是否崩溃（journalctl / docker logs）
  ├─ 进程在但只绑 127.0.0.1，代理在另一网络命名空间？
  │    └─ 容器/主机网络模型问题
  └─ 进程在、端口对，但仍 502
       └─ 看应用启动未完成、TLS 指错、超时过短
```

**最小复现笔记模板**（建议写进 `notes.md`）：

```markdown
## 现象
- 时间：
- URL：
- 状态码：

## 已检查
- [ ] 进程
- [ ] 端口
- [ ] 代理配置
- [ ] 最近部署
- [ ] 应用日志最后 50 行摘要

## 结论 / 下一步
```

---

## 附录：权限位速记

```text
rwx rwx rwx
owner group other

6 = rw-
5 = r-x
0 = ---

600 = 仅 owner 读写 → 密钥文件常用
644 = owner 读写，其他人只读 → 普通配置（仍勿放密钥）
755 = 目录常见（可进入）
777 = 人人可读写执行 → 密钥场景禁止
```

示例验收：

```bash
printf 'APP_API_KEY=fake\n' > fake.env
chmod 600 fake.env
stat -c '%a %n' fake.env 2>/dev/null || stat -f '%A %N' fake.env
# 期望看到 600
```

---

## 附录：自检

- [ ] 能独立完成「建目录 → 写日志 → grep → tail」
- [ ] 能解释 `chmod 600` 的必要性
- [ ] 能说出 502 + 端口无人听时的前三步
- [ ] 能区分 `export` 的作用域


---

## 附录：Windows / WSL 提示

1. 命令题优先在 WSL Ubuntu 里做，避免 PowerShell 与 Linux 工具差异干扰学习目标。
2. 仓库若在 `/mnt/c/...`，注意文件权限与 `chmod` 表现可能与原生 Linux 不一致；关键权限练习可在 WSL 自家目录复制一份文件做。
3. `ss` 若缺失：`sudo apt update && sudo apt install -y iproute2`。
4. `python -m http.server` 在 WSL 中监听后，Windows 浏览器访问 `http://127.0.0.1:8765` 通常可用（视版本/端口转发而定）。

**口头题**：为什么密钥文件不要 777？`export` 的变量另一个新终端看得到吗？

### 一页速通脚本（可整段粘贴）

```bash
set -euo pipefail
mkdir -p /tmp/pyday-linux/demo/a/b
printf 'agent status=ok
findme-rag
' > /tmp/pyday-linux/demo/a/b/app.log
grep -n 'findme-rag' /tmp/pyday-linux/demo/a/b/app.log
tail -n 2 /tmp/pyday-linux/demo/a/b/app.log
printf 'APP_API_KEY=fake
' > /tmp/pyday-linux/fake.env
chmod 600 /tmp/pyday-linux/fake.env
ls -l /tmp/pyday-linux/fake.env
```


---

## 附录：把输出记进笔记的模板

```markdown
# B2 进程与端口

## 启动命令
python -m http.server 8765

## ps 摘要
（粘贴关键一行）

## ss/netstat 摘要
（粘贴监听行）

## curl 摘要
HTTP/1.0 200 OK
```

再补三条「我下次会先看什么」的个人习惯即可过关。

> 本章通过线：B1～B4 笔记齐全，并能口述权限与端口排障。

<!-- end -->
