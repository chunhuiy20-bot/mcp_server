"""
    通用ai服务api
    对于服务最好原子化，方便调用和管理，避免不必要的耦合
"""
import json
from typing import Any

from fastapi import Request
from fastapi import Query
from langgraph.graph.state import CompiledStateGraph

from config.router.CustomRouter import CustomAPIRouter
from schemas.common.Result import Result
from schemas.ybbl.ai_school.vo.PersonalityReportVo import TalentReportResponse
from xiaoyan.agent.workflow.PersonaConstructorWorkflow import persona_constructor_workflow
from xiaoyan.agent.workflow2.CommonWorkflow import CreateWorkflowDto, common_workflow
from xiaoyan.rpc.XiaoYanRPCClient import xiao_yan_api_rpc_client

router = CustomAPIRouter(
    prefix="/api/ai/xiaoyan",
    tags=["XiaoYan 项目接口"]
)


async def start_report_scheduled_Task_func():
    print(f"[定时任务] 开启定时获取聊天记录并总结报告任务...")
    print(await persona_constructor_workflow.report_scheduled_Task())




async def start_report_scheduled_Task_func2():
    """
    配置驱动的工作流编译器的方式执行定时任务
    :return
    """
    # 1、远程调用获取用于与ai的聊天记录
    result = await xiao_yan_api_rpc_client.get_history_chat()
    if result.code != 200 and result.code != 0:
        return Result(code=result.code, message="获取聊天记录失败")
    if len(result.data.history_chat_list) <= 0:
        return Result(code=200, message="聊天记录为空", data=[])

    print(f"获取到 {len(result.data.history_chat_list)} 个用户的聊天记录，开始并行处理...")
    # 2、 加载配置
    create_workflow_dto = CreateWorkflowDto(config_type="file",
                                            config="../agent/workflow2/persona_constructor_workflow.json")
    # 3、 创建工作流
    workflow = await common_workflow.create_workflow(create_workflow_dto)

    # 3、创建所有任务
    tasks = [
        workflow.ainvoke({
            "user_history_chat_list": user_chat.chat_history,
            "analysis_results": [],
            "final_report": None,
            "user_id": user_chat.user_id
        })
        for user_chat in result.data.history_chat_list
    ]

    # 4、并发执行所有任务
    report_results = await asyncio.gather(*tasks, return_exceptions=True)
    print(report_results)

    success_count = 0
    for i, result in enumerate(report_results):
        if isinstance(result, Exception):
            print(f"用户信息处理失败")
        else:
            success_count += 1
            print("=============0==========")
            print(result["final_report"])
            data = result["final_report"].model_dump(by_alias=True, exclude_none=True)
            data["user_id"] = result["user_id"]
            print(type(data))
            print(data)
            t = TalentReportResponse(**data)
            print(t)
            print(await xiao_yan_api_rpc_client.submit_user_profile(profile=data))


    print(f"处理完成: 成功 {success_count}/{len(report_results)}")



if __name__ == "__main__":
    import asyncio
    asyncio.run(start_report_scheduled_Task_func2())


@router.post(path="/scheduler/start_report_scheduled_Task",
             response_model=Result[dict],
             summary="开启定时获取聊天记录并总结报告任务",
             description="开启定时获取聊天记录并总结报告任务",
             )
async def start_report_scheduled_Task(request: Request, seconds: int = Query(default=300, description="清理间隔（秒）", ge=5,  le=86400,  example=300), job_id: str = Query(default="start_report_scheduled_Task", description="任务ID", example="start_report_scheduled_Task")) -> Result[dict]:
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
