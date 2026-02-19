"""
2grok2api 应用入口

FastAPI 应用初始化和路由注册
"""

from contextlib import asynccontextmanager
import os
import platform
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Ensure the project root is on sys.path (helps when Vercel sets a different CWD)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi import Depends  # noqa: E402

from app.core.auth import verify_api_key  # noqa: E402
from app.core.config import get_config  # noqa: E402
from app.core.logger import logger, setup_logging  # noqa: E402
from app.core.exceptions import register_exception_handlers  # noqa: E402
from app.core.response_middleware import ResponseLoggerMiddleware  # noqa: E402
from app.api.v1.chat import router as chat_router  # noqa: E402
from app.services.token import get_scheduler  # noqa: E402

# 初始化日志
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"), json_console=False, file_logging=True
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 1. 注册服务默认配置
    from app.core.config import config, register_defaults
    from app.services.grok.defaults import get_grok_defaults

    register_defaults(get_grok_defaults())

    # 2. 加载配置
    await config.load()

    # 3. 启动服务显示
    logger.info("Starting 2grok2api...")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Python: {sys.version.split()[0]}")

    # 4. 启动 Token 刷新调度器
    refresh_enabled = get_config("token.auto_refresh", True)
    if refresh_enabled:
        basic_interval = get_config("token.refresh_interval_hours", 8)
        super_interval = get_config("token.super_refresh_interval_hours", 2)
        interval = min(basic_interval, super_interval)
        scheduler = get_scheduler(interval)
        scheduler.start()

    logger.info("Application startup complete.")
    yield

    # 关闭
    logger.info("Shutting down 2grok2api...")

    from app.core.storage import StorageFactory

    if StorageFactory._instance:
        await StorageFactory._instance.close()

    if refresh_enabled:
        scheduler = get_scheduler()
        scheduler.stop()


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="2grok2api",
        lifespan=lifespan,
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 请求日志和 ID 中间件
    app.add_middleware(ResponseLoggerMiddleware)

    # 注册异常处理器
    register_exception_handlers(app)

    # 仅暴露 chat/completions
    app.include_router(
        chat_router, prefix="/v1", dependencies=[Depends(verify_api_key)]
    )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "9765"))
    workers = int(os.getenv("SERVER_WORKERS", "1"))

    # 平台检查
    is_windows = platform.system() == "Windows"

    # 自动降级
    if is_windows and workers > 1:
        logger.warning(
            f"Windows platform detected. Multiple workers ({workers}) is not supported. "
            "Using single worker instead."
        )
        workers = 1

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=os.getenv("LOG_LEVEL", "INFO").lower(),
    )
