# Linux 基础

> 所属模块：`08-devops-architecture` · 部署、运维与软件架构  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/08-devops-architecture/01-linux-basics.md`](../../exercises/08-devops-architecture/01-linux-basics.md)

## 本章定位

- **模块目标**：具备把服务跑起来、拆清楚边界的能力。
- **本章角色**：掌握服务器排障最小命令集——看进程、看日志、懂权限与环境变量。
- **说明**：Windows 本机可用 WSL2 / 远程 Linux / 云主机练习；重点是概念可迁移。

## 学习目标

1. 会用一组高频命令完成目录、文件、检索操作。
2. 能查看进程与日志，定位「服务是否在跑」。
3. 理解权限位与环境变量对服务的影响。
4. 对 systemd 有基本直觉。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 常用命令、进程与日志、权限与环境 | 能上机排小障 |
| **建议掌握** | systemd 直觉 | 知道服务如何托管 |
| **了解即可** | 性能排查工具链 | 地图 |

---

## 1. 为什么要学

Agent 上线后问题长这样：

```text
接口 502 —— 进程挂了？端口没听？
LLM 调用失败 —— 环境变量 Key 没注入？
磁盘满 —— 日志打爆了？
```

不会 Linux 基础，就只能「重启试试」。

---

## 2. 必掌握：常用命令

```bash
pwd                 # 当前目录
ls -la              # 列表（含隐藏）
cd /path
mkdir -p a/b
cp -r src dst
mv a b
rm -rf dir          # 危险，先确认路径
cat file | less
head -n 50 file
tail -n 100 file
tail -f app.log     # 跟随日志
grep -R "ERROR" .   # 递归搜
find . -name "*.log"
curl -i http://127.0.0.1:8000/health
```

编辑：`nano` / `vim`（会一种即可）。

压缩：

```bash
tar -czf out.tar.gz dir
tar -xzf out.tar.gz
```

---

## 3. 必掌握：进程与日志

```bash
ps aux | grep uvicorn
pgrep -a uvicorn
kill <pid>          # 先温柔；不行再 kill -9（慎用）
ss -ltnp            # 看监听端口（或 netstat）
```

日志从哪来：

- 应用自己写的文件（`logging`）
- 容器日志：`docker logs`
- systemd：`journalctl -u service`

习惯：

```text
先看是否存活 → 再看端口 → 再看最近错误日志
```

---

## 4. 必掌握：权限与环境

### 权限

```bash
ls -l
# -rwxr-xr-x  owner group ...
chmod 600 .env      # 仅本人读写密钥文件
chown user:group file
```

服务不要用 root 跑业务（习惯上）。

### 环境变量

```bash
export APP_API_KEY=xxx
echo $APP_API_KEY
env | grep APP_
```

systemd / Docker / 平台控制台都会注入环境变量；**进程看不到你在另一个 shell 里 export 的值**，除非写进服务配置。

---

## 5. 建议掌握：systemd 直觉

```text
/etc/systemd/system/my-agent.service
→ systemctl daemon-reload
→ systemctl enable --now my-agent
→ systemctl status my-agent
→ journalctl -u my-agent -f
```

unit 文件里常有：`ExecStart=`、`Environment=`、`WorkingDirectory=`、`Restart=`。  
云上也可能是平台托管，不必自己写 unit——但概念相同：自动拉起、崩溃重启、集中看日志。

---

## 6. 了解即可：性能排查工具链

`top`/`htop`、`iostat`、`vmstat`、`perf`……先会看 CPU/内存是否打满即可。

---

## 7. 常见坑

1. 改了代码但旧进程还在
2. `.env` 权限过于开放
3. 磁盘被日志填满
4. 时区混乱导致时间戳难读（优先 UTC 存）

---

## 8. 练习指引

[`exercises/08-devops-architecture/01-linux-basics.md`](../../exercises/08-devops-architecture/01-linux-basics.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能用 ls/cd/grep/tail/curl 完成基础操作
- [ ] 能查进程与端口
- [ ] 知道密钥文件权限与环境变量作用域

### 下一章

[`02-docker-deploy.md`](./02-docker-deploy.md) —— 用容器把 Agent 服务打包跑起来。

## 导航

- 返回模块：[README](./README.md)
- 下一章：[Docker 与部署](./02-docker-deploy.md)
