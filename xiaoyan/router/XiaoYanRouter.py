"""
    通用ai服务api
    对于服务最好原子化，方便调用和管理，避免不必要的耦合
"""
import asyncio
from fastapi import Request
from fastapi import Query
from config.router.CustomRouter import CustomAPIRouter
from schemas.common.Result import Result
from xiaoyan.agent.workflow.PersonaConstructorWorkflow import persona_constructor_workflow

router = CustomAPIRouter(
    prefix="/api/ai/xiaoyan",
    tags=["TongXin 项目接口"]
)

async def start_report_scheduled_Task_func():
    print(f"[定时任务] 开启定时获取聊天记录并总结报告任务...")
    print(await persona_constructor_workflow.report_scheduled_Task())


@router.post(path="/scheduler/start_report_scheduled_Task",
             response_model=Result[dict],
             summary="开启定时获取聊天记录并总结报告任务",
             description="开启定时获取聊天记录并总结报告任务",
             )
async def start_report_scheduled_Task(request: Request,
                             seconds: int = Query(default=300, description="清理间隔（秒）", ge=5,  le=86400,  example=300),
                             job_id: str = Query(default="start_report_scheduled_Task", description="任务ID", example="start_report_scheduled_Task")) -> Result[dict]:
    """
    启动清理任务
    :param job_id: 定时任务id，没事不要改
    :param request:
    :param seconds: 定时清理时间间隔
    """
    scheduler = request.app.state.scheduler
    # 添加清理任务 - 每5分钟执行一次
    job_id = scheduler.add_interval_job(
        func=start_report_scheduled_Task_func,
        seconds=seconds,
        job_id=job_id,
        replace_existing=True
    )

    return Result(
        code=200,
        message="清理任务已启动",
        data={
            "job_id": job_id,
            "interval_seconds": seconds
        }
    )


# 获取所有定时任务
@router.get(path="/scheduler/jobs",
            response_model=Result[list],
            summary="获取所有定时任务",
            description="获取所有定时任务")
async def get_all_jobs(request: Request) -> Result[list]:
    """获取所有定时任务"""

    scheduler = request.app.state.scheduler
    jobs = scheduler.get_jobs()

    return Result(data=jobs, message="获取任务列表成功", code=200)


@router.delete(path="/scheduler/stop/jobs",
               response_model=Result[dict],
               summary="停止指定定时任务",
               description="根据job_id来停止指定定时任务")
async def remove_job(request: Request, job_id: str = Query(default="cleanup_expired_agents", example="cleanup_expired_agents", description="定时任务ID")) -> Result[dict]:
    """
    删除指定任务
    @:param job_id
    """
    scheduler = request.app.state.scheduler
    success = scheduler.remove_job(job_id)
    if not success:
        return Result(
            code=500,
            message="任务不存在",
            data={
                "job_id": job_id
            }
        )
    return Result(
        code=200,
        message="任务已删除",
        data={
            "job_id": job_id
        }
    )
