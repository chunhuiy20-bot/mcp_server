from fastapi import FastAPI
from contextlib import asynccontextmanager
from config.scheduler.DynamicScheduler import scheduler
from xiaoyan.router.XiaoYanRouter import router as xiao_yan_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("FastAPI应用启动，初始化调度器...")
    scheduler.start()

    # scheduler.add_interval_job(
    #     func=custom_task,
    #     seconds=5000,
    #     job_id="custom_task_5s"
    # )

    yield
    # 关闭时
    print("FastAPI应用关闭，停止调度器...")
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
# 将调度器实例添加到app状态中，供路由使用
app.include_router(xiao_yan_router)
app.state.scheduler = scheduler  # type: ignore
