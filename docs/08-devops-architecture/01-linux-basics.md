# Linux 基础

> 所属模块：`08-devops-architecture` · 部署、运维与软件架构  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有 WSL / 远程 Linux / 云主机可上手；进程/日志/权限/环境变量建议动手踩一遍）  
> 对应练习：[`exercises/08-devops-architecture/01-linux-basics.md`](../../exercises/08-devops-architecture/01-linux-basics.md)

## 本章定位

- **模块目标**：具备把服务跑起来、拆清楚边界的能力。
- **本章角色**：掌握服务器排障最小命令集——看进程、看端口、看日志、懂权限与环境变量；对 systemd 有基本直觉。
- **你的优势**：模块 04 已有进程/fd 直觉；模块 03/06 写过 logging 与 FastAPI 服务——本章把这些概念落到「在 Linux 上怎么查」。
- **说明**：Windows 本机可用 WSL2 / 远程 Linux / 云主机练习；重点是概念可迁移，不是背发行版差异。
- **目标不是**：成为全职 SRE；够用、能对话、能把 Agent 服务从「502 懵了」推到「知道查哪三处」。

## 学习目标（学完应能做到）

1. 会用一组高频命令完成目录、文件、检索、压缩与健康检查。
2. 能查看进程与监听端口，判断「服务是否在跑、听在哪个地址」。
3. 能从应用日志 / `journalctl` /（预告）容器日志里抓最近错误。
4. 理解权限位与环境变量作用域对服务的影响；会给 `.env` 收紧权限。
5. 对 systemd 的 enable / start / status / journal 有基本直觉。
6. 对 CPU/内存/磁盘排查工具链建立地图（了解即可）。
7. 完成课后练习，能按「存活 → 端口 → 日志 → 环境」排小障。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | 常用命令、进程与日志、权限与环境 | 能上机排小障；命令能默写常用组合 |
| **建议掌握** | systemd 直觉 | 知道服务如何托管、崩溃如何看日志 |
| **了解即可** | 性能排查工具链 | 建立地图；CPU/内存打满时知道先看谁 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要 Linux 基础？

Agent 上线后问题很少再是「Python 语法错了」，而长这样：

```text
接口 502 —— 进程挂了？端口没听？上游超时？
LLM 调用失败 —— 环境变量 Key 没注入？权限读不到 .env？
磁盘满 —— 日志打爆了？临时文件没清？
改了代码仍旧行为 —— 旧进程还在跑？
```

不会这一套，就只能「重启试试」；会这一套，你会按固定剧本推进。

#### 没有这些技能时，排障会长这样

```text
「服务挂了」→ 不知道用 ps / ss 还是看日志
「Key 明明 export 了」→ 不知道 systemd/Docker 进程看不到你 shell 里的变量
「日志在哪」→ 不知道应用文件 / journalctl / docker logs 三套来源
「权限报错」→ 不知道 600/644/755 对密钥与脚本意味着什么
```

#### 本章要练的四种能力

1. **定位现场**：进程在不在、端口在不听、最近错误是什么
2. **管好秘密**：密钥文件权限、环境变量注入位置
3. **读懂托管**：systemd（及后续 Docker）如何拉起与重启
4. **建立地图**：性能工具链知道名字与用途，不深挖

可以先记一句：

> Linux 排障的最小闭环：**存活 → 端口 → 日志 → 环境/权限**。

#### Windows / WSL / 前端对照（先建立地图）

| 你熟悉的场景 | 本章对应 |
| --- | --- |
| Windows「任务管理器」看进程 | `ps` / `pgrep` / `top` |
| 资源监视器看端口占用 | `ss -ltnp` / `netstat` |
| 前端 DevTools Network 看请求是否通 | `curl -i` 打 `/health` |
| Node 里 `process.env.API_KEY` | shell `export` / systemd `Environment=` / Docker `-e` |
| Windows 服务（自动启动） | systemd unit |
| PowerShell / CMD | bash（WSL 或远程 Linux） |

**练习环境建议**：优先 WSL2（Ubuntu）或一台小云主机；纯 Windows 原生也能理解概念，但命令题请尽量进 Linux shell。

---

## 2. 必掌握：常用命令

这一节会刻意写细——后面查日志、改权限、打包配置都建立在这组「手感」上。

### 2.1 目录与文件：先站稳脚跟

#### 为什么需要？

上服务器第一件事不是改配置，而是知道「我在哪、有什么、能不能写」。路径错一步，`rm` 与 `chmod` 都会变成事故。

#### 怎么用

```bash
pwd                 # 当前工作目录（绝对路径）
ls                  # 列出当前目录
ls -la              # 含隐藏文件 + 权限/所有者详情
cd /path/to/dir     # 进入目录；cd - 回到上一次
cd ~                # 回家目录
mkdir -p a/b/c      # 递归创建；已存在不报错（-p）
touch notes.txt     # 创建空文件或更新时间戳
cp file dst         # 复制文件
cp -r src dst       # 递归复制目录
mv a b              # 重命名或移动
rm file             # 删文件
rm -rf dir          # 递归强制删目录——危险，先确认 pwd 与路径
```

阅读文件（由浅到深）：

```bash
cat file            # 整文件刷到终端（小文件）
less file           # 分页看；q 退出
head -n 50 file     # 前 50 行
tail -n 100 file    # 后 100 行
tail -f app.log     # 跟随追加（排障神器）
```

#### 跑一下

在练习目录（或任意可写目录）执行：

```bash
mkdir -p demo/a/b
echo "hello agent" > demo/a/b/note.txt
pwd
ls -la demo/a/b
cat demo/a/b/note.txt
```

预期：

- `pwd` 打印你当前绝对路径
- `ls -la` 能看到 `note.txt`，左侧有类似 `-rw-r--r--` 的权限串
- `cat` 输出 `hello agent`

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `rm -rf` 前不看 `pwd` | 删错目录，可能不可恢复 |
| 用 `cat` 看巨大日志 | 终端刷爆、卡死；用 `tail`/`less` |
| 相对路径凭感觉敲 | 实际在别的 cwd，文件「找不到」或写到别处 |
| Windows 路径习惯 `\a\b` | Linux 用 `/`；WSL 里 Windows 盘在 `/mnt/c/...` |

#### Windows / WSL 对照

| 动作 | PowerShell / CMD（粗对照） | bash |
| --- | --- | --- |
| 当前目录 | `pwd` / `cd` | `pwd` |
| 列表 | `dir` / `Get-ChildItem` | `ls -la` |
| 进目录 | `cd` | `cd` |
| 建目录 | `mkdir` | `mkdir -p` |
| 看文件尾 | `Get-Content -Tail` | `tail -n` / `tail -f` |

---

### 2.2 检索：grep 与 find

#### 为什么需要？

Agent 日志里常有 `ERROR`、`Traceback`、`429`、`timeout`。不会搜，就只能肉眼滚屏。

#### 怎么用

```bash
grep "ERROR" app.log              # 单文件搜
grep -n "ERROR" app.log           # 带行号
grep -i "error" app.log           # 忽略大小写
grep -R "ERROR" .                 # 当前目录递归
grep -R --include="*.log" "ERROR" .
find . -name "*.log"              # 按文件名找
find . -name "*.log" -mtime -1    # 近 1 天改过的 log（了解）
```

组合拳（很常用）：

```bash
grep -R "Traceback" . --include="*.log" | head -n 20
tail -n 200 app.log | grep -i "timeout"
```

#### 跑一下

```bash
mkdir -p demo/logs
printf 'INFO start\nERROR llm timeout\nINFO ok\n' > demo/logs/app.log
grep -n "ERROR" demo/logs/app.log
find demo -name "*.log"
```

预期：

- `grep` 打出带 `ERROR llm timeout` 的那一行（`-n` 时前面有行号）
- `find` 列出 `demo/logs/app.log`

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `grep -R` 扫整个 `/` 或超大仓库 | 又慢又吵；先 `cd` 到服务目录 |
| 只搜 `error` 小写且不加 `-i` | 漏掉 `ERROR` / `Error` |
| 用 `find` 当 `grep` | `find` 找文件；`grep` 找内容 |

#### 前端对照

| 前端习惯 | Linux |
| --- | --- |
| VS Code / Cursor 全局搜索 | `grep -R` |
| 按文件名过滤 `*.log` | `find -name` / `grep --include` |
| 看 Network 里失败请求文案 | 在日志里 grep 状态码与 timeout |

---

### 2.3 健康检查：curl

#### 为什么需要？

进程在、不等于接口通。Agent / FastAPI 通常有 `/health` 或根路径；`curl` 是最短路径的「从机器上确认 HTTP」。

#### 怎么用

```bash
curl -i http://127.0.0.1:8000/health
# -i 打印响应头 + 正文；看 HTTP/1.1 200 还是 502

curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/health
# 只看状态码（脚本友好）

curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hi"}'
```

连不上时常见输出：`Connection refused`（没人听端口）或超时（防火墙/听在别的地址）。

#### 跑一下

另开一个终端先起一个最小服务，再测：

```bash
# 终端 A
python -m http.server 8765

# 终端 B
curl -i http://127.0.0.1:8765/
```

预期：响应头里有 `HTTP/1.0 200 OK`（或类似），正文是目录列表 HTML。  
然后 `Ctrl+C` 停掉 A，再 `curl` 一次——应变成 `Connection refused`。这就是「端口没人听」的现场感。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只信浏览器，不上服务器本机 `curl` | 分不清是 DNS/网关问题还是进程本身挂了 |
| 打错端口或打了 `localhost` 但服务绑在别的网卡 | 误判「服务挂了」 |
| 把 HTML 错误页当 JSON API 成功 | 后面解析炸掉；先看状态码与 `Content-Type` |

#### 前端对照

| 前端 | 服务器上 |
| --- | --- |
| 浏览器地址栏 / DevTools | `curl -i` |
| `fetch('/health')` | 同路径的 HTTP GET |
| axios 看 `status` | `curl -w "%{http_code}"` |

---

### 2.4 编辑与压缩（够用即可）

#### 为什么需要？

改 unit、改 `.env`、打一份配置包发给同事——不必精通 vim，但要能落地。

#### 怎么用

编辑（会一种即可）：

```bash
nano file.txt       # 新手友好；Ctrl+O 保存，Ctrl+X 退出
vim file.txt        # 会用更好；不会可先用 nano
```

压缩与解压：

```bash
tar -czf out.tar.gz dir     # 打包并 gzip
tar -xzf out.tar.gz         # 解压到当前目录
tar -tzf out.tar.gz         # 只看包内列表，不解开
```

#### 跑一下

```bash
mkdir -p demo/pkg
echo "cfg=1" > demo/pkg/app.env
tar -czf demo/out.tar.gz -C demo pkg
tar -tzf demo/out.tar.gz
mkdir -p demo/unpacked && tar -xzf demo/out.tar.gz -C demo/unpacked
cat demo/unpacked/pkg/app.env
```

预期：`tar -tzf` 能看到 `pkg/app.env`；解压后 `cat` 输出 `cfg=1`。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 解压前不看 `tar -tzf` | 文件散落当前目录，污染工作区 |
| 把密钥打进 tar 再随处传 | 泄漏；打包前检查内容 |
| 在 Windows 资源管理器解 `.tar.gz` 后再传回 WSL | 权限/换行可能被改；优先在 Linux 侧操作 |

---

### 2.5 常用命令速查卡

排障时先回到这张卡：

```bash
pwd / ls -la / cd / mkdir -p
cp -r  mv  rm   # rm 先确认
head / tail / tail -f / less
grep -R "ERROR" . --include="*.log"
find . -name "*.log"
curl -i http://127.0.0.1:8000/health
tar -czf out.tar.gz dir && tar -xzf out.tar.gz
```

---

## 3. 必掌握：进程与日志

这一节对接 Agent 服务排障主路径：**先确认进程与端口，再读最近错误**。

### 3.1 进程：谁在跑？

#### 为什么需要？

「接口 502」的第一嫌疑人经常是：uvicorn / gunicorn / 你的 `python -m` **根本没在跑**，或跑了多个旧实例。

#### 怎么用

```bash
ps aux | grep uvicorn          # 粗搜；可能看到 grep 自己
ps aux | grep -v grep | grep uvicorn
pgrep -a uvicorn               # 更干净：PID + 命令行
pgrep -af "uvicorn|gunicorn|python.*agent"
```

结束进程：

```bash
kill <pid>                     # 默认 SIGTERM：请进程自己收尾
# 等几秒再看是否还在
kill -9 <pid>                  # SIGKILL：强杀；可能留锁文件/半截写——慎用
```

习惯：先 `kill`，确认还在再用 `-9`；生产上优先用 systemd / 容器编排的 stop，而不是随手杀。

#### 跑一下

```bash
# 终端 A
python -m http.server 8765

# 终端 B
pgrep -a "http.server"
ps aux | grep -v grep | grep "http.server"
```

预期：能看到一条带 `python -m http.server 8765` 的进程行，最前或靠前有 PID。  
记下 PID 后：

```bash
kill <pid>
pgrep -a "http.server" || echo "gone"
```

预期：第二次 `pgrep` 无输出，或打印 `gone`。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 改了代码但没重启进程 | 旧代码仍在服务请求 |
| 同时起两个绑定同一端口的实例 | 后起的失败，或你 curl 到的不是你以为的那个 |
| 一上来 `kill -9` | 跳过优雅关闭；DB 连接/临时文件可能不干净 |
| `grep uvicorn` 匹配到无关行 | 用 `pgrep -a` 或更具体的命令行模式 |

#### Windows / 前端对照

| 场景 | 做法 |
| --- | --- |
| Windows | 任务管理器结束进程；或 PowerShell `Get-Process` |
| 前端本地 `npm run dev` | 关终端 / Ctrl+C ≈ 结束进程；残留占用端口时要查 PID |
| 模块 04「进程容器」 | 这里的每一行 `ps` 就是一个进程实例 |

---

### 3.2 端口：谁在听？

#### 为什么需要？

进程在，但可能：

- 听在 `127.0.0.1` 而外部访问不到
- 听在 `8000` 而网关转去了 `8001`
- 根本没 bind 成功（启动日志里有 `Address already in use`）

#### 怎么用

```bash
ss -ltnp                     # 监听中的 TCP，显示进程（需权限时 PID 可能是 `-`）
ss -ltnp | grep 8000
# 若无 ss：
netstat -ltnp                # 旧工具，部分系统仍可用
```

字段直觉：

```text
Local Address:Port   → 听在哪（0.0.0.0:8000 表示所有网卡）
Process              → 哪个 PID/命令占用
```

#### 跑一下

```bash
# 终端 A
python -m http.server 8765

# 终端 B
ss -ltnp | grep 8765
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/
```

预期：`ss` 能看到 `:8765`；`curl` 打印 `200`。  
停掉服务后再 `ss` / `curl`，端口消失，`curl` 变为连接失败。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只看进程、不看端口 | 进程是「别的东西」，或听错端口 |
| 假设 `localhost` 与 `0.0.0.0` 对外表现相同 | 容器/云安全组场景差异很大 |
| 无权限时看不到进程名就放弃 | 至少能确认「有没有人听该端口」 |

---

### 3.3 日志从哪来？

#### 为什么需要？

进程与端口只能回答「活没活」；**为什么挂、为什么 500**，要靠日志。

Agent 服务常见三类来源：

| 来源 | 典型命令 / 路径 | 何时出现 |
| --- | --- | --- |
| 应用自己写的文件 | `tail -f /var/log/my-agent/app.log` 或项目下 `logs/` | 你用了 `logging` 配 FileHandler |
| systemd 托管 | `journalctl -u my-agent -f` | 用 unit 跑服务（本章 §5） |
| 容器 | `docker logs -f <container>` | 下一章 Docker；先记「还有这条路径」 |

标准输出若被 systemd/Docker 接管，**不一定**落在你以为的文件里——所以「日志在哪」要先问启动方式。

#### 怎么用（应用日志）

```bash
tail -n 100 app.log
tail -f app.log
grep -n "ERROR\|Traceback\|timeout\|429" app.log | tail -n 50
less +G app.log          # 打开并跳到末尾（若支持）
```

和 Python `logging` 的对应（模块 03）：

```text
logging.info / error  → 进你配置的 Handler
没配文件 Handler     → 可能只在 stdout → journalctl / docker logs
```

#### 跑一下（模拟一份 Agent 错误日志）

```bash
mkdir -p demo/logs
cat > demo/logs/agent.log <<'EOF'
2026-10-21T10:00:01Z INFO  app started
2026-10-21T10:00:02Z INFO  listening on 0.0.0.0:8000
2026-10-21T10:01:10Z ERROR llm call failed: timeout after 30s
2026-10-21T10:01:10Z ERROR Traceback (most recent call last):
2026-10-21T10:01:11Z INFO  request id=abc done status=500
EOF

tail -n 3 demo/logs/agent.log
grep -n "ERROR\|timeout" demo/logs/agent.log
```

预期：能稳定抽出 timeout / ERROR 行；这就是线上「先看最近错误」的缩小版。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只看文件日志，服务其实由 systemd 管 | 文件是空的或很旧，真相在 `journalctl` |
| 不看时间戳 | 把昨天的 ERROR 当成当前故障 |
| 日志级别长期 DEBUG 且不轮转 | 磁盘被打满（见常见坑） |
| 在日志里打印 API Key / Authorization | 泄密；打码或禁止记录敏感头 |

---

### 3.4 Agent 服务排障剧本（必背顺序）

把命令串成固定顺序——练习 A1 会要求你写类似剧本：

```text
1. 存活：pgrep / ps  → 进程在吗？命令行是不是你以为的那个？
2. 端口：ss -ltnp    → 端口在听吗？地址是 127.0.0.1 还是 0.0.0.0？
3. 探测：curl -i     → 本机 HTTP 是否 200？还是连接拒绝 / 5xx？
4. 日志：tail / journalctl / docker logs → 最近 ERROR / Traceback？
5. 环境：env / unit / 平台变量 → Key、数据库 URL 是否在该进程可见？
```

502 场景对照：

| 观察 | 优先怀疑 |
| --- | --- |
| 进程不在 | 崩溃未拉起；OOM；部署失败 |
| 进程在、端口不在 | 启动失败；听错端口；绑定失败 |
| 端口在、curl 5xx | 应用异常；依赖（DB/LLM）挂；看日志 |
| curl 本机 200、对外 502 | 网关/反代/安全组/上游配置（下一层基础设施） |
| LLM 相关 500 且日志 timeout/401 | 环境变量、配额、网络超时（联模块 04/09） |

#### 跑一下（半模拟 502）

```bash
# 没有服务听 8000 时：
curl -i http://127.0.0.1:8000/health || true
ss -ltnp | grep 8000 || echo "nothing on 8000"
```

预期：`curl` 失败（连接拒绝）；`ss` 无监听。  
这就是「网关若把流量转到这台机器的 8000，用户就会看到 502」的本机侧真相。

---

## 4. 必掌握：权限与环境

### 4.1 权限位：谁能读你的密钥？

#### 为什么需要？

`.env` 里常有 `OPENAI_API_KEY` / 数据库密码。权限过于开放（如 `777`/`666`），同机其他用户或被入侵账户可能直接读走。

#### 怎么理解

`ls -l` 看到的串：

```text
-rwxr-xr-x  1 alice alice  123 Oct 21 10:00 start.sh
│││││││││
││││││││└── 其他人：x（执行）
│││││││└─── 其他人：r
││││││└──── 其他人：-（无写）
│││││└───── 组：x
││││└────── 组：r
│││└─────── 组：-
││└──────── 所有者：x
│└───────── 所有者：w
└────────── 所有者：r
首位：- 文件；d 目录；l 链接
```

数字模式（常用）：

| 模式 | 含义 | 典型用途 |
| --- | --- | --- |
| `600` | 仅所有者读写 | `.env`、私钥 |
| `644` | 所有者读写，其他人只读 | 普通配置（无秘密） |
| `755` | 所有者可执行，其他人读/执行 | 脚本、目录 |
| `700` | 仅所有者可进目录 | 私密目录 |

#### 怎么用

```bash
ls -l .env
chmod 600 .env              # 收紧密钥文件
chmod 755 start.sh          # 脚本可执行
chown user:group file       # 改所有者（常需 sudo）
```

习惯：**业务服务尽量不用 root 跑**；用专用用户 + 最小权限。

#### 跑一下

```bash
mkdir -p demo/secret
printf 'APP_API_KEY=sk-demo-not-real\n' > demo/secret/.env
chmod 600 demo/secret/.env
ls -l demo/secret/.env
```

预期：权限串类似 `-rw-------`，即 `600`。  
对比（仅在练习目录演示，勿对真密钥这样玩太久）：

```bash
chmod 644 demo/secret/.env
ls -l demo/secret/.env
chmod 600 demo/secret/.env
```

观察：`644` 时组与其他人有 `r`——密钥文件应避免。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `.env` 使用 `777` / `666` | 秘密暴露面过大 |
| 用 root 跑 Agent 只为「省事」 | 一旦被 RCE，损失放大 |
| 在 Windows 编辑后拷进 WSL | 权限可能变松；进 WSL 后重新 `chmod 600` |
| 把 `.env` 提交进 git | 与文件权限无关也会泄漏（工程章已强调） |

#### 前端对照

| 前端 | 服务器 |
| --- | --- |
| `.env` 不进仓库、Vercel/平台注入 | 文件 `chmod 600` + systemd/Docker 注入 |
| 浏览器端**不能**放真密钥 | 密钥只留在服务端进程环境 |

---

### 4.2 环境变量：进程看不见你「另一个 shell」的 export

#### 为什么需要？

LLM 调用失败里，经典一句是：「我明明 `export APP_API_KEY=...` 了」。  
真相：环境变量是**进程维度**的；子进程继承创建它时的环境；**别的终端、systemd 服务、Docker 容器默认都看不到你在 A 终端 export 的值**。

#### 怎么用

```bash
export APP_API_KEY=xxx
echo "$APP_API_KEY"
env | grep APP_
unset APP_API_KEY
```

在 Python 里（对照）：

```python
import os

print(os.environ.get("APP_API_KEY"))  # 没有则 None
```

注入位置要对齐启动方式：

| 启动方式 | 变量应写在哪 |
| --- | --- |
| 前台手动跑 | 同一 shell 里 `export`，或 `APP_API_KEY=xxx python ...` |
| systemd | unit 的 `Environment=` / `EnvironmentFile=` |
| Docker | `docker run -e` / compose `environment` / `env_file` |
| 云平台 | 控制台「环境变量」配置 |

#### 跑一下（作用域实验——对应练习 B4）

```bash
# 终端 A
export DEMO_VAR=1
echo "A sees DEMO_VAR=$DEMO_VAR"

# 终端 B（新开一个）
echo "B sees DEMO_VAR=${DEMO_VAR:-<empty>}"
```

预期：A 打印 `1`；B 打印 `<empty>`（或空）。  
结论：**export 不是「整台机器全局配置」**。

再验证「子进程能继承」：

```bash
export DEMO_VAR=1
python -c "import os; print(os.environ.get('DEMO_VAR'))"
```

预期：打印 `1`。因为这个 `python` 是当前 shell 的子进程。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 在 A 终端 export，去看 B 终端的服务 | 服务进程没有该变量 |
| 改了 unit 的环境变量却没 `daemon-reload` + 重启 | 旧进程仍用旧环境 |
| 在日志/截图里打印完整 Key | 泄漏 |
| 以为写了 `.env` 文件就自动进任何进程 | 需要应用或托管层显式加载 |

#### Windows / WSL 对照

| 环境 | 注意 |
| --- | --- |
| PowerShell | `$env:APP_API_KEY="xxx"` 只影响当前会话 |
| WSL | WSL 与 Windows 环境变量不自动等同；在 WSL 内重新 export / 配服务 |
| IDE Run Configuration | IDE 启动的进程用 IDE 配的 env，不是你外部 shell 的 |

---

### 4.3 权限 × 环境：Agent 密钥检查清单

上线前快速过一遍：

```text
[ ] .env 或密钥文件权限是 600（或等价）
[ ] 服务用户能读该文件（所有者/ACL 正确）
[ ] 真正跑服务的进程环境里有 APP_API_KEY（不是你的交互 shell）
[ ] 日志/错误信息不会回显完整密钥
[ ] .env 不在 git 仓库中
```

验证「服务进程是否带上变量」的思路：

```bash
# 若知道 PID
tr '\0' '\n' < /proc/<pid>/environ | grep APP_
# 无权限或非 Linux 时：看 unit / compose / 启动脚本更实际
```

了解即可：`/proc/<pid>/environ` 是 Linux 特有排障技巧；WSL 里通常可用。

---

## 5. 建议掌握：systemd 直觉

### 5.1 为什么需要 systemd？

笔记本前台跑 `uvicorn`，关终端就停。服务器需要：

```text
开机自启
崩溃后自动拉起
集中看状态与日志
用非交互方式注入环境变量与工作目录
```

systemd 用 **unit 文件**描述这些。云平台/容器编排可能替你做同一件事——概念相同：**托管、重启策略、日志出口**。

### 5.2 最小心智图

```text
写 /etc/systemd/system/my-agent.service
  → sudo systemctl daemon-reload      # 让 systemd 重新读配置
  → sudo systemctl enable my-agent    # 开机自启
  → sudo systemctl start my-agent     # 现在启动
  # 或：sudo systemctl enable --now my-agent
  → systemctl status my-agent         # 看 Active、PID、最近日志摘要
  → journalctl -u my-agent -f         # 跟随该服务日志
```

常用子命令：

| 命令 | 作用 |
| --- | --- |
| `systemctl start/stop/restart NAME` | 启停重启 |
| `systemctl enable/disable NAME` | 是否开机自启 |
| `systemctl status NAME` | 当前状态 |
| `systemctl daemon-reload` | 改过 unit 文件后必做 |
| `journalctl -u NAME -n 100` | 最近 100 行 |
| `journalctl -u NAME --since "10 min ago"` | 按时间切片 |

### 5.3 unit 里常看的字段

教学用最小示例（**不要**原样当生产模板，密钥管理与用户要加强）：

```ini
[Unit]
Description=My Agent API
After=network.target

[Service]
Type=simple
User=agent
WorkingDirectory=/opt/my-agent
Environment=APP_ENV=prod
EnvironmentFile=-/opt/my-agent/.env
ExecStart=/opt/my-agent/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

字段直觉：

| 字段 | 含义 |
| --- | --- |
| `ExecStart=` | 真正启动命令（绝对路径更稳） |
| `WorkingDirectory=` | 进程 cwd；影响相对路径读配置 |
| `Environment=` / `EnvironmentFile=` | 注入环境变量（对接 §4） |
| `Restart=` | 崩溃是否拉起 |
| `User=` | 用谁跑——避免 root |

`EnvironmentFile=` 前的 `-` 表示文件不存在时不致失败（细节因版本而异；先建立「可从文件读环境」的印象）。

### 5.4 跑一下（地图级——无 root 时改书面推演）

若你有一台可练的 Linux/WSL 且具备 sudo，可按下面做**最小验证**；若没有，用书面走通练习 A2 即可。

```bash
# 1）假设已放置 my-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now my-agent

# 2）看状态
systemctl status my-agent --no-pager

# 3）看日志
journalctl -u my-agent -n 50 --no-pager
journalctl -u my-agent -f
# Ctrl+C 结束跟随
```

预期：`status` 里 `Active: active (running)`；`journalctl` 能看到 uvicorn/应用启动日志。  
然后人为 `stop`，再 `curl` 端口——应连接失败；再 `start`，恢复。

无完整项目时，可用「假服务」建立肌肉记忆（示例）：

```bash
# 仅演示 journal 与 status 概念时，也可观察系统已有服务：
systemctl status cron.service --no-pager 2>/dev/null \
  || systemctl status crond.service --no-pager 2>/dev/null \
  || echo "skip: no cron unit in this environment"
```

### 5.5 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 改了 unit 忘了 `daemon-reload` | 行为仍是旧配置 |
| `enable` 了但没 `start` | 重启机器后才有，当前仍没跑 |
| `Environment=` 写在错误 shell 里以为服务能读到 | 只有 unit/平台注入的才进服务进程 |
| `WorkingDirectory` 不对 | 相对路径读文件失败 |
| 只看 `status` 绿就结案 | 仍要用 `curl` + 应用日志确认业务健康 |
| 与 Docker 混用两套托管抢同一端口 | 端口冲突；选一个编排者 |

### 5.6 Windows / 平台对照

| 系统 | 对应直觉 |
| --- | --- |
| Windows 服务 | 自动启动 + 后台托管 |
| `pm2` / `supervisor` | 另一类进程托管；概念类似 |
| Kubernetes / 云 Run | 平台替你做 restart 与日志收集 |
| Docker Compose `restart:` | 容器级重启策略（下一章） |

可以先记一句：

> 不必人人手写 unit，但要能读懂「谁在拉起进程、崩溃谁负责、日志出口在哪」。

---

## 6. 了解即可：性能排查工具链

CPU 打满、内存飙高、磁盘写爆——先会「看仪表」，再按需学深工具。

### 6.1 地图：先看什么

| 现象 | 先看 | 常见工具 |
| --- | --- | --- |
| 机器整体卡、响应慢 | CPU / 负载 | `top` / `htop` |
| Agent 变慢、疑似泄漏 | 内存 RES/RSS | `top` / `free -h` |
| 日志/下载把盘写满 | 磁盘空间与 inode | `df -h` / `du -sh` |
| 偶发抖、iowait 高 | 磁盘 I/O | `iostat`（sysstat 包） |
| 要挖函数级热点 | 性能剖析 | `perf` 等（进阶） |

本章目标：

> 会看 CPU/内存是否打满、磁盘是否满；把 `perf` 留在地图边缘即可。

### 6.2 跑一下（只建立手感）

```bash
# 负载与进程（q 退出；无 htop 时用 top）
top -b -n 1 | head -n 20

free -h
df -h .
```

预期：

- `top` 头部有 load average、CPU、内存摘要；下列进程按资源排序
- `free -h` 显示内存与 swap
- `df -h .` 显示当前磁盘分区使用率——**接近 100% 要警惕日志打满**

可选观察：

```bash
du -sh /var/log 2>/dev/null || du -sh demo/logs
```

### 6.3 和 Agent 的弱联系（预告）

```text
CPU 长期 100%  → 是否同步狂打 LLM？是否死循环解析？
内存持续涨    → history/缓存无限涨（联模块 04）
磁盘满        → 日志未轮转；临时上传未清理
iowait 高     → 磁盘慢或同步狂写日志
```

更深的 profiling、APM、分布式追踪留给工程化与生产可观测专题；这里只要知道「先看顶层资源再下钻」。

### 6.4 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 一看慢就加机器 | 可能是磁盘满或单进程死循环 |
| 忽略 swap / OOM | 进程被杀，只看到「突然没了」 |
| 只看 CPU，不看磁盘 | 日志打满时服务乱失败 |

---

## 7. 常见坑（全章对照表）

| # | 坑 | 正确习惯 |
| --- | --- | --- |
| 1 | 改了代码但旧进程还在 | 重启托管进程；用 `pgrep`/`ss` 确认新 PID/端口 |
| 2 | `.env` 权限过于开放 | `chmod 600`；最小权限用户跑服务 |
| 3 | 磁盘被日志填满 | 轮转（logrotate 等）；控制级别；监控 `df` |
| 4 | 时区混乱导致时间戳难读 | 存储与日志优先 UTC；展示层再本地化 |
| 5 | 在 A shell export，以为服务进程有变量 | 把变量写进 unit / Docker / 平台配置并重启 |
| 6 | 只看进程不看端口 | `ss -ltnp` + `curl -i` |
| 7 | 日志看错出口 | 分清文件 / `journalctl` / `docker logs` |
| 8 | 一上来 `kill -9` | 先 TERM；交给 systemd/容器 stop |
| 9 | `rm -rf` 前不看 `pwd` | 先 `pwd`/`ls`，路径写绝对路径更稳 |
| 10 | 本机 curl 通就当用户侧一定通 | 还要考虑反代、安全组、听绑定地址 |

---

## 8. 练习指引

请打开并完成：

[`exercises/08-devops-architecture/01-linux-basics.md`](../../exercises/08-devops-architecture/01-linux-basics.md)

建议实验位置（命令笔记可放这里）：

```text
playground/08-devops-architecture/01-linux-basics/
```

建议动手顺序：

1. **B1** 命令速通：`mkdir` / 写文件 / `grep` / `tail`（§2）  
2. **B2** 进程与端口：`python -m http.server` + `ps`/`ss`/`curl`（§3）  
3. **B3** `.env` + `chmod 600` + `ls -l`（§4.1）  
4. **B4** 两终端验证环境变量作用域（§4.2）  
5. 有余力：**A1** 写「502 + 端口没人听」五步剧本（§3.4）；**A2** systemd 地图（§5）；**C1** 日志轮转认知（§6 / 常见坑）

做题时始终对照四步：**存活 → 端口 → 日志 → 环境/权限**。

---

## 9. 小结与下一站

### 心智模型

```text
排障闭环：
  进程在吗？→ 端口在听吗？→ curl 通吗？→ 最近错误日志？→ 环境/权限对吗？

命令最小集：
  ls/cd/mkdir/cp/mv/rm  head/tail/grep/find  curl  tar
  ps/pgrep/kill  ss  chmod/chown  export/env
  systemctl / journalctl（托管场景）

密钥：
  文件权限收紧 + 变量注入到「真正的服务进程」

性能：
  先看 top / free / df；打满再下钻
```

### 和前端 / Windows 经验的最终对照

| 你熟悉的事 | 本章对应 |
| --- | --- |
| 任务管理器 / 结束进程 | `ps` / `kill` / systemd stop |
| DevTools 看请求是否 200 | `curl -i` |
| `process.env` / 平台环境变量 | export / unit / Docker / 控制台 |
| 本地 dev server 占端口 | `ss -ltnp` |
| Windows 服务自启 | systemd enable |

### 自检清单

- [ ] 能用 `ls`/`cd`/`grep`/`tail`/`curl` 完成基础操作
- [ ] 能查进程与端口，并解释 Connection refused
- [ ] 知道应用日志 / journalctl / docker logs 三种出口
- [ ] 知道密钥文件权限与环境变量作用域
- [ ] 能说出 systemd 的 enable/start/status/journalctl 各自干什么
- [ ] 知道 CPU/内存/磁盘打满时先看哪些命令（了解级）
- [ ] 独立完成练习基础题 B1～B4

### 一句话带走

> Agent 服务排障，先用 Linux 最小命令集确认「进程、端口、日志、环境」，再谈加机器或改架构。

### 下一章

[`02-docker-deploy.md`](./02-docker-deploy.md) —— 用容器把 Agent 服务打包跑起来（镜像、compose、与日志/环境变量对接）。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一模块：[数据库与数据持久化](../07-data-persistence/README.md)
- 下一章：[Docker 与部署](./02-docker-deploy.md)
