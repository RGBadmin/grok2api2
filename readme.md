# 2grok2api

> `2grok2api` 是基于原项目 [`chenyme/grok2api`](https://github.com/chenyme/grok2api) 的二次开发版本。
>
> 本仓库保留 OpenAI 兼容接口形态，并针对实际部署与客户端兼容做了定向改造。

**中文** | [English](docs/README.en.md)

---

## 项目来源与定位

- 上游项目：`chenyme/grok2api`
- 当前项目：`RGBadmin/2grok2api`
- 目标：
  - 保持 OpenAI 兼容调用体验（重点 `/v1/chat/completions`）
  - 适配本地/容器化部署
  - 修复多种客户端“图片空白/只显示空消息”的兼容问题

---

## 相对上游的主要改动

### 1) 部署与工程改造

- 项目对外名称统一为 **2grok2api**
- 默认端口统一为 **9765**
- `docker-compose` 改为**本地源码 build**（不再依赖上游远程镜像）
- service/container/image 名称统一为 `2grok2api`
- 修复容器内 `uvicorn: not found` 相关依赖安装问题

### 2) 路由策略调整

- 保留 OpenAI 兼容核心接口：`/v1/chat/completions`
- 同时保留常用页面与管理入口（如 `/admin`、静态资源、文件访问等）
- 保留 `/v1/models`

### 3) 图片返回链路（重点）

围绕 `grok-imagine-1.0` 在聊天客户端中的显示兼容，做了以下改造：

- 默认通过 `/v1/chat/completions` 输出图片结果
- 输出形态改为 Markdown 图片格式：
  - `![image](https://.../v1/files/image/xxx.jpg)`
- 流式输出改为 OpenAI 风格 chunk + `[DONE]`
- 仅返回最终结果图（优先 final/jpg）
- 忽略中间预览图（如 medium/png）
- 收到中间图后，若 **50 秒**内未收到最终图，返回：`生成失败请重试`
- 上游异常时避免直接抛 500 给客户端，尽量返回可读失败信息

### 4) 图片外链地址配置增强

新增并优先支持：

- `app.public_base_url`

用于生成对外可访问图片 URL（优先级高于 `app.app_url`），适合反代/CDN/多层网络场景。

---

## 快速开始

### 本地运行

```bash
uv sync
uv run main.py
```

### Docker Compose

```bash
git clone https://github.com/RGBadmin/2grok2api
cd 2grok2api
docker compose up -d --build
```

---

## 管理面板

- 地址：`http://<host>:9765/admin`
- 默认密码：`2grok2api`（配置项 `app.app_key`，请上线后立即修改）

---

## 核心接口示例

### 聊天/图片统一入口

`POST /v1/chat/completions`

```bash
curl http://localhost:9765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -d '{
    "model": "grok-imagine-1.0",
    "stream": false,
    "messages": [
      {"role":"user","content":"画一只在窗边晒太阳的橘猫"}
    ]
  }'
```

成功时 `choices[0].message.content` 形如：

```text
![image](https://your-domain/v1/files/image/xxxx-final.jpg)
```

---

## 配置建议

在反向代理或公网部署场景，建议至少设置：

- `app.app_key`：后台登录密码
- `app.api_key`：API 鉴权密钥
- `app.public_base_url`：公网可访问基地址（用于图片 URL）

---

## 致谢与声明

- 感谢上游 `chenyme/grok2api` 的开源工作。
- 本项目为二次开发版本，欢迎提交 Issue / PR。
- 请在遵守服务条款与法律法规前提下使用，禁止非法用途。

## 开源协议

本项目沿用与上游项目 `chenyme/grok2api` 相同的开源协议：**MIT License**。

- 上游仓库：`chenyme/grok2api`
- 本仓库：`RGBadmin/2grok2api`
- 详细条款见仓库根目录 [`LICENSE`](./LICENSE)

二次开发、分发与商用请遵守 MIT 协议要求，并保留原始版权与许可声明。

