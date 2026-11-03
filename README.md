# 氢能可研报告 Agent

氢能项目资料与可研报告大纲工具，包含 FastAPI 后端和 Next.js 前端。

## 当前功能

- 后端：PDF、DOCX、Markdown、TXT 资料上传与解析，报告创建与列表，大纲生成、编辑、增删和排序。
- 正式前端：报告列表、搜索、刷新，以及加载、空数据和错误状态；读取真实后端数据。
- 正式前端的上传、创建与大纲编辑入口目前显示功能说明，尚未接入操作。可使用后端临时验收界面或 API 体验已有后端能力。
- 全文生成、审计、重写、正文编辑和 Word 导出尚未实现。

尚未接入登录和用户权限隔离。

## 获取代码

```bash
git clone https://github.com/Mat11-oo/hydrogen-feasibility-agent.git
cd hydrogen-feasibility-agent
```

私有仓库需要使用具有访问权限的 GitHub 账号。

## 启动后端

在仓库根目录执行：

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

如需生成大纲，在 `backend/.env` 填入 `MODEL_API_KEY`；模型端点和模型名称可沿用示例。不要把真实密钥提交到 GitHub。

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --port 8000
```

- 报告列表 API：`GET /api/v1/reports`
- 临时验收界面：`/`
- 接口文档：`/docs`

## 启动前端

保持后端运行，在另一个终端进入仓库的 `frontend` 目录：

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

前端服务端从 `.env.local` 读取 `BACKEND_URL`，请配置为实际后端服务地址；前端无需配置模型密钥。

生产构建与启动：

```bash
npm run build
npm run start
```

## 测试与检查

后端离线测试（从仓库根目录执行）：

```bash
cd backend
MODEL_API_KEY="" .venv/bin/python -m pytest -q
```

前端检查（从仓库根目录执行）：

```bash
cd frontend
npm test -- --run
npm run lint
npm run typecheck
npm run build
```

真实模型冒烟（从仓库根目录执行，需要配置真实 Key，产生模型调用费用）：

```bash
backend/.venv/bin/python scripts/smoke.py hydrogen-feasibility-agent 阶段3-1
```

该脚本在隔离的临时数据库中验证后端大纲生成、保存与回读；运行记录生成在 `docs/evidence/`，不会提交到仓库。它不表示正式前端已接通大纲生成功能。

## 数据与目录

```text
backend/app/       后端接口、业务逻辑、模型调用和数据结构
backend/static/    后端临时验收界面
backend/tests/     后端测试
frontend/          正式前端源码、测试和依赖锁文件
scripts/           模型冒烟与重启恢复脚本
```

数据库与上传文件默认保存在 `data/`。仓库排除真实环境文件、业务数据、虚拟环境、依赖目录和构建产物，仅保留无密钥的 `.env.example`。

本仓库仅包含项目代码及本 README，不包含需求文档、开发文档、设计参考和验收截图。
