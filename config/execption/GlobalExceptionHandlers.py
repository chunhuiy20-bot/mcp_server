"""
异常处理器模块
"""
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理请求参数验证错误(422)
    """
    # 提取第一个错误信息
    error_detail = exc.errors()[0] if exc.errors() else {}
    field = error_detail.get('loc', ['unknown'])[-1]  # 获取字段名
    msg = error_detail.get('msg', '参数验证失败')

    # 自定义友好的错误消息
    custom_error_messages = {
        'string_too_long': f'参数 {field} 长度超出限制',
        'string_too_short': f'参数 {field} 长度不足',
        'value_error': f'参数 {field} 格式不正确',
        'type_error': f'参数 {field} 类型错误',
        'missing': f'缺少必需参数 {field}',
        'string_pattern_mismatch': f'参数 {field} 格式不符合要求'
    }

    error_type = error_detail.get('type', '')
    error_msg = custom_error_messages.get(error_type, f'参数 {field} 验证失败: {msg}')

    return JSONResponse(
        status_code=400,
        content={
            "code": 400,
            "message": error_msg,
            "data": None
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    logging.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None
        }
    )


def register_exception_handlers(app):
    """注册所有异常处理器"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)