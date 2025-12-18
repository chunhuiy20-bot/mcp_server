import os
import socket
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from nacos import NacosClient


class FastApiWithNacos:
    """轻量可复用的 FastAPI + Nacos 启动类"""

    def __init__(self, routers: List[APIRouter], *, title: str = None, version: str = "1.0.0"):
        # ---- 基本配置 ----
        self.nacos_server = os.getenv("NACOS_SERVER", "8.130.81.134:8848")
        self.nacos_username = os.getenv("NACOS_USERNAME", "nacos")
        self.nacos_password = os.getenv("NACOS_PASSWORD", "haoduanduan2025@.")
        self.nacos_namespace = os.getenv("NACOS_NAMESPACE", "")

        self.service_name = os.getenv("SERVICE_NAME", title or "hdd-ai-module")
        self.service_group = os.getenv("SERVICE_GROUP", "DEFAULT_GROUP")
        self.port = int(os.getenv("SERVICE_PORT", 8000))
        self.ip = os.getenv("SERVICE_IP", self._get_local_ip())
        self.ephemeral = os.getenv("EPHEMERAL", "true").lower() == "true"

        # ---- 初始化 Nacos 客户端 ----
        self.client: Optional[NacosClient] = None
        self._init_nacos_client()

        # ---- 创建 FastAPI 应用 ----
        self.app = FastAPI(
            title=title or self.service_name,
            version=version,
            lifespan=self._lifespan
        )

        # ---- 挂载路由 ----
        self._register_routes(routers)

    def _init_nacos_client(self):
        """初始化 Nacos 客户端"""
        try:
            self.client = NacosClient(
                server_addresses=self.nacos_server,
                namespace=self.nacos_namespace,
                username=self.nacos_username,
                password=self.nacos_password
            )
            print(f"Nacos client initialized: {self.nacos_server}")
        except Exception as e:
            print(f"Failed to initialize Nacos client: {e}")
            self.client = None

    def _get_local_ip(self) -> str:
        """自动探测本地 IP"""
        # try:
        #     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        #         s.connect(("8.8.8.8", 80))
        #         return s.getsockname()[0]
        # except Exception:
        #     return "127.0.0.1"
        return "127.0.0.1"

    def _register_routes(self, routers: List[APIRouter]):
        """统一注册外部注入的路由"""
        for router in routers:
            self.app.include_router(router)


    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """应用生命周期管理"""
        # 启动时注册服务
        await self._register_to_nacos()
        yield
        # 关闭时注销服务
        await self._deregister_from_nacos()

    async def _register_to_nacos(self):
        """注册服务到 Nacos"""
        if not self.client:
            print("Nacos client not initialized, skipping registration")
            return

        print(f"Registering {self.service_name} to Nacos ({self.nacos_server})")
        try:
            self.client.add_naming_instance(
                service_name=self.service_name,
                ip=self.ip,
                port=self.port,
                group_name=self.service_group,
                weight=1.0,
                ephemeral=self.ephemeral,
                heartbeat_interval=5,
                metadata={
                    "version": "1.0.0",
                    "framework": "FastAPI",
                    "preserved.register.source": "SPRING_CLOUD"
                },
                enable=True,
                healthy=True
            )
            print("✅ Service registered to Nacos successfully")
        except Exception as e:
            print(f"❌ Nacos registration failed: {e}")

    async def _deregister_from_nacos(self):
        """从 Nacos 注销服务"""
        if not self.client:
            return

        print(f"Deregistering {self.service_name} from Nacos")
        try:
            self.client.remove_naming_instance(
                service_name=self.service_name,
                ip=self.ip,
                port=self.port,
                group_name=self.service_group
            )
            print("✅ Service deregistered from Nacos successfully")
        except Exception as e:
            print(f"❌ Nacos deregistration failed: {e}")

    def get_app(self) -> FastAPI:
        """获取 FastAPI 应用实例"""
        return self.app

    def run(self, **kwargs):
        """启动应用"""
        import uvicorn

        # 默认配置
        config = {
            "host": "0.0.0.0",
            "port": self.port,
            "reload": False,
            "log_level": "info"
        }

        # 合并用户配置
        config.update(kwargs)

        print(f"Starting {self.service_name} on {config['host']}:{config['port']}")
        uvicorn.run(self.app, **config)