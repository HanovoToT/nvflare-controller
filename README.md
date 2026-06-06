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

## API 端点

### 服务状态
- `GET /api/v1/status` - 获取所有服务状态

### Dashboard 管理
- `POST /api/v1/dashboard/start` - 启动 Dashboard
- `POST /api/v1/dashboard/stop` - 停止 Dashboard
- `GET /api/v1/dashboard/status` - Dashboard 状态

### POC 管理
- `POST /api/v1/poc/prepare` - 准备 POC 环境
- `POST /api/v1/poc/start` - 启动 POC
- `POST /api/v1/poc/stop` - 停止 POC（同时停止 Server 和所有 Clients）
- `GET /api/v1/poc/status` - POC 状态

### Server/Client 管理
- `POST /api/v1/poc/server/start` - 启动 Server
- `POST /api/v1/poc/server/stop` - 停止 Server
- `POST /api/v1/poc/clients` - 添加 Client（组织默认为 nvidia）
- `POST /api/v1/poc/clients/<name>/start` - 启动 Client
- `POST /api/v1/poc/clients/<name>/stop` - 停止 Client
- `POST /api/v1/poc/clients/start-n` - 启动 N 个 Client
- `POST /api/v1/poc/clients/stop-all` - 停止所有 Client

### Jobs
- `GET /api/v1/jobs` - 获取 Job 列表
- `POST /api/v1/jobs` - 提交 Job (multipart/form-data)
- `GET /api/v1/jobs/<job_id>/log` - 获取 Job 日志
- `POST /api/v1/jobs/<job_id>/abort` - 中止 Job

### 设置
- `GET /api/v1/settings` - 获取配置
- `POST /api/v1/settings` - 保存配置

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

### Job 提交方式

使用 NVFlare CLI 而非 REST API：
- `nvflare job submit -j <job.zip>` - 提交 Job（自动解压 zip）
- `nvflare job list` - 列出 Jobs
- `nvflare job abort --force <job_id>` - 中止 Job

### 进程管理

- Dashboard: 通过 `python -m nvflare.dashboard.application` 启动
- POC/Server/Client: 通过 `nvflare poc` 系列命令管理
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

## 上传 GitHub

```bash
cd /Users/h/Desktop/testPlugin/nvflare-controller
gh repo create nvflare-controller --public --source=. --push
```