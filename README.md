# NVFlare Controller

独立控制器，用于管理 NVFlare Dashboard、POC 环境、Server 和 Client 进程。
**完全独立，不修改 NVFlare 源码。**

## 功能特性

- **Dashboard 管理** - 启动/停止 NVFlare Dashboard
- **POC 环境管理** - prepare/start/stop POC 环境
- **Server/Client 管理** - 独立启动/停止 Server 和 Client
- **Job 提交** - 通过 NVFlare CLI 提交 Job（不依赖 REST API）
- **凭证管理** - 动态读取配置文件中的登录凭证

## 安装

```bash
cd nvflare-controller
pip install -e .
```

## 启动

```bash
export NVFLARE_CONTROLLER_PORT=8080
python3 -m nvflare_controller.app
```

## 访问

- 控制面板: http://localhost:8080
- API 状态: http://localhost:8080/api/v1/status

## 控制面板功能

### Dashboard 管理
- 启动/停止 Dashboard
- 查看运行状态和 PID

### POC 环境管理
-准备 POC 环境（prepare）
- 启动 POC（start）
- 停止 POC（stop）- 同时关闭 Server 和所有 Clients

### Server/Client 管理
- 独立启动/停止 Server
- 添加新 Client（组织默认为 nvidia）
- 独立启动/停止单个 Client
- 启动 N 个 Client
- 停止所有 Client

### Job 管理
- 上传 Job ZIP 文件提交
- 查看 Job 列表
- 获取 Job 日志
- 中止运行中的 Job

### 设置
- 配置 Dashboard 端口
- 配置登录凭证（邮箱/密码/组织）
- 配置 NVFlare 源码路径
- 配置 Python 解释器路径
- 配置 POC 工作目录

## 配置

配置文件位于 `~/.nvflare-controller/config.json`:

```json
{
  "dashboard_port": 8443,
  "credential": "admin@example.com:123456:org",
  "nvflare_path": "/path/to/nvflare",
  "python_exe": "/usr/bin/python3",
  "poc_workspace": "/tmp/nvflare/poc"
}
```

### 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `dashboard_port` | Dashboard 端口 | 8443 |
| `credential` | 登录凭证 (email:password:org) | admin@example.com:123456:org |
| `nvflare_path` | NVFlare 源码路径（用于 PYTHONPATH） | 空 |
| `python_exe` | Python 解释器路径 | /usr/bin/python3 |
| `poc_workspace` | POC 工作目录 | /tmp/nvflare/poc |

## 技术架构

### 底层实现

全部使用 NVFlare CLI 命令，不依赖 Dashboard REST API：

| 功能 | CLI 命令 |
|------|----------|
| 准备 POC | `nvflare poc prepare -n <num> --force` |
| 启动 POC | `nvflare poc start --no-wait` |
| 停止 POC | `nvflare poc stop --no-wait` |
| 添加 Client | `nvflare poc add-site <name> --org <org>` |
| 提交 Job | `nvflare job submit -j <folder>` |
| 列出 Jobs | `nvflare job list` |
| 中止 Job | `nvflare job abort --force <job_id>` |

### 进程管理

- Dashboard: 通过 `python -m nvflare.dashboard.application` 启动
- Server/Client: 直接调用 startup.sh 脚本
- 凭证变化时自动重置数据库

### 前端特性

- 标签页状态保存在 localStorage，刷新不丢失
- 设置保存需要二次确认
- Client 组织字段默认为 nvidia

## 项目结构

```
nvflare_controller/
├── app.py              # Flask 应用入口
├── config.py           # 配置管理
├── process_manager.py  # 子进程管理
├── api_client.py       # CLI Job 客户端
└── routes/
    ├── dashboard.py    # Dashboard 管理
    ├── poc.py          # POC/Server/Client 管理
    ├── jobs.py         # Job 管理
    └── settings.py     # 设置
```