from fastmcp import FastMCP
import asyncio
from datetime import datetime
from typing import Optional
import random

mcp = FastMCP(name="TransactionMCP", instructions="""
资金流水管理工具。
此工具专注于交易流水的CRUD操作，用户身份由调用方（AI服务）管理。
支持的操作：
- 添加收支流水
- 查询流水记录  
- 更新流水信息
- 删除流水记录
流水类型：1=支出，2=收入
""")

# 模拟数据存储（内存中的假数据）
fake_transactions = {}  # {user_id: [transactions]}
transaction_id_counter = 1000


def get_user_transactions(user_id: int):
    """获取用户的交易记录"""
    if user_id not in fake_transactions:
        fake_transactions[user_id] = []
    return fake_transactions[user_id]


@mcp.tool()
async def add_transaction(user_id: int, transaction_category_id: int, transaction_name: str, transaction_amount: float, type: int, transaction_time: str = None, remark: str = None) -> str:
    """
    添加资金流水记录

    Args:
        user_id: 用户ID（由AI服务传入）
        transaction_category_id: 流水分类ID (餐饮=1, 交通=2, 购物=3, 娱乐=4, 工资=100)
        transaction_name: 交易流水名称
        transaction_amount: 金额
        type: 分类（1：支出 2：收入）
        transaction_time: 交易时间（可选，格式：YYYY-MM-DD HH:MM:SS）
        remark: 备注（可选）

    Returns:
        添加结果
    """
    global transaction_id_counter

    # 验证参数
    if type not in [1, 2]:
        return "❌ 错误：type 必须是 1（支出）或 2（收入）"

    if transaction_amount <= 0:
        return "❌ 错误：金额必须大于0"

    try:
        # 生成交易ID
        transaction_id = transaction_id_counter
        transaction_id_counter += 1

        # 创建交易记录
        transaction_data = {
            "id": transaction_id,
            "user_id": user_id,
            "transaction_category_id": transaction_category_id,
            "transaction_name": transaction_name,
            "transaction_account": transaction_amount,
            "type": type,
            "transaction_time": transaction_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "remark": remark,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "del_flag": "0"
        }

        # 添加到用户的交易记录中
        user_transactions = get_user_transactions(user_id)
        user_transactions.append(transaction_data)

        type_name = "💸支出" if type == 1 else "💰收入"
        category_names = {1: "餐饮", 2: "交通", 3: "购物", 4: "娱乐", 100: "工资"}
        category_name = category_names.get(transaction_category_id, "其他")

        return f"✅ 成功添加{type_name}流水：{transaction_name}，金额：{transaction_amount}元\n📂 分类：{category_name}\n🆔 流水ID：{transaction_id}"

    except Exception as e:
        return f"❌ 添加流水时发生错误：{str(e)}"


@mcp.tool()
async def query_transactions(user_id: int, limit: int = 10, type: Optional[int] = None, start_date: str = None, end_date: str = None) -> str:
    """
    查询用户流水记录

    Args:
        user_id: 用户ID（由AI服务传入）
        limit: 查询条数限制，默认10条
        type: 流水类型筛选（1：支出 2：收入，不填查询全部）
        start_date: 开始日期（可选，格式：YYYY-MM-DD）
        end_date: 结束日期（可选，格式：YYYY-MM-DD）

    Returns:
        流水记录列表
    """
    try:
        # 获取用户交易记录
        user_transactions = get_user_transactions(user_id)

        # 如果用户没有交易记录，添加一些示例数据
        if not user_transactions:
            sample_transactions = [
                {
                    "id": random.randint(1, 999),
                    "user_id": user_id,
                    "transaction_category_id": 1,
                    "transaction_name": "午餐",
                    "transaction_account": 25.0,
                    "type": 1,
                    "transaction_time": "2024-12-18 12:30:00",
                    "remark": "公司附近餐厅",
                    "create_time": "2024-12-18 12:30:00",
                    "del_flag": "0"
                },
                {
                    "id": random.randint(1, 999),
                    "user_id": user_id,
                    "transaction_category_id": 100,
                    "transaction_name": "月薪",
                    "transaction_account": 8000.0,
                    "type": 2,
                    "transaction_time": "2024-12-01 09:00:00",
                    "remark": "12月工资",
                    "create_time": "2024-12-01 09:00:00",
                    "del_flag": "0"
                },
                {
                    "id": random.randint(1, 999),
                    "user_id": user_id,
                    "transaction_category_id": 2,
                    "transaction_name": "地铁",
                    "transaction_account": 4.0,
                    "type": 1,
                    "transaction_time": "2024-12-18 08:30:00",
                    "remark": "上班通勤",
                    "create_time": "2024-12-18 08:30:00",
                    "del_flag": "0"
                }
            ]
            user_transactions.extend(sample_transactions)

        # 过滤条件
        filtered_transactions = user_transactions.copy()

        # 按类型过滤
        if type:
            filtered_transactions = [t for t in filtered_transactions if t["type"] == type]

        # 按日期过滤（简单实现）
        if start_date:
            filtered_transactions = [t for t in filtered_transactions
                                     if t["transaction_time"] >= start_date]
        if end_date:
            filtered_transactions = [t for t in filtered_transactions
                                     if t["transaction_time"] <= end_date + " 23:59:59"]

        # 按时间倒序排列
        filtered_transactions.sort(key=lambda x: x["transaction_time"], reverse=True)

        # 限制数量
        filtered_transactions = filtered_transactions[:limit]

        if not filtered_transactions:
            return "📝 未找到符合条件的流水记录"

        # 格式化输出
        output = f"📊 找到 {len(filtered_transactions)} 条流水记录：\n\n"

        total_income = 0
        total_expense = 0

        for i, trans in enumerate(filtered_transactions, 1):
            type_name = "💸支出" if trans["type"] == 1 else "💰收入"

            if trans["type"] == 1:
                total_expense += trans["transaction_account"]
            else:
                total_income += trans["transaction_account"]

            output += f"{i}. {trans['transaction_name']} - {type_name}\n"
            output += f"   💰 金额：{trans['transaction_account']}元\n"
            output += f"   🕐 时间：{trans['transaction_time']}\n"
            if trans.get('remark'):
                output += f"   📝 备注：{trans['remark']}\n"
            output += f"   🆔 ID：{trans['id']}\n\n"

        # 添加统计信息
        if len(filtered_transactions) > 1:
            output += "📈 统计信息：\n"
            if total_income > 0:
                output += f"💰 总收入：{total_income}元\n"
            if total_expense > 0:
                output += f"💸 总支出：{total_expense}元\n"
            if total_income > 0 and total_expense > 0:
                balance = total_income - total_expense
                output += f"💳 净收支：{balance:+.2f}元\n"

        return output

    except Exception as e:
        return f"❌ 查询流水时发生错误：{str(e)}"


@mcp.tool()
async def update_transaction(user_id: int, transaction_id: int, transaction_name: str = None, transaction_amount: float = None, remark: str = None) -> str:
    """
    更新流水记录

    Args:
        user_id: 用户ID（由AI服务传入）
        transaction_id: 流水记录ID
        transaction_name: 新的交易名称（可选）
        transaction_amount: 新的金额（可选）
        remark: 新的备注（可选）

    Returns:
        更新结果
    """
    try:
        user_transactions = get_user_transactions(user_id)

        # 查找要更新的交易
        transaction_to_update = None
        for trans in user_transactions:
            if trans["id"] == transaction_id and trans["user_id"] == user_id:
                transaction_to_update = trans
                break

        if not transaction_to_update:
            return f"❌ 未找到流水记录 ID: {transaction_id}，或该记录不属于当前用户"

        # 更新字段
        updated_fields = []
        if transaction_name:
            transaction_to_update["transaction_name"] = transaction_name
            updated_fields.append(f"名称: {transaction_name}")

        if transaction_amount:
            if transaction_amount <= 0:
                return "❌ 错误：金额必须大于0"
            transaction_to_update["transaction_account"] = transaction_amount
            updated_fields.append(f"金额: {transaction_amount}元")

        if remark is not None:  # 允许设置空备注
            transaction_to_update["remark"] = remark
            updated_fields.append(f"备注: {remark or '(已清空)'}")

        if not updated_fields:
            return "❌ 没有提供要更新的字段"

        # 更新时间
        transaction_to_update["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"✅ 成功更新流水记录 ID: {transaction_id}\n📝 更新内容: {', '.join(updated_fields)}"

    except Exception as e:
        return f"❌ 更新流水时发生错误：{str(e)}"


@mcp.tool()
async def delete_transaction(user_id: int, transaction_id: int) -> str:
    """
    删除流水记录（软删除）

    Args:
        user_id: 用户ID（由AI服务传入）
        transaction_id: 流水记录ID

    Returns:
        删除结果
    """
    try:
        user_transactions = get_user_transactions(user_id)

        # 查找要删除的交易
        transaction_to_delete = None
        for trans in user_transactions:
            if trans["id"] == transaction_id and trans["user_id"] == user_id:
                transaction_to_delete = trans
                break

        if not transaction_to_delete:
            return f"❌ 未找到流水记录 ID: {transaction_id}，或该记录不属于当前用户"

        # 软删除
        transaction_to_delete["del_flag"] = "1"
        transaction_to_delete["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        type_name = "支出" if transaction_to_delete["type"] == 1 else "收入"
        return f"✅ 成功删除{type_name}流水记录\n📝 {transaction_to_delete['transaction_name']} - {transaction_to_delete['transaction_account']}元\n🆔 ID: {transaction_id}"

    except Exception as e:
        return f"❌ 删除流水时发生错误：{str(e)}"


@mcp.tool()
async def get_user_summary(user_id: int, days: int = 30) -> str:
    """
    获取用户流水汇总信息

    Args:
        user_id: 用户ID（由AI服务传入）
        days: 统计天数，默认30天

    Returns:
        汇总信息
    """
    try:
        user_transactions = get_user_transactions(user_id)

        if not user_transactions:
            return "📊 暂无流水记录"

        # 过滤有效记录（未删除）
        valid_transactions = [t for t in user_transactions if t["del_flag"] == "0"]

        if not valid_transactions:
            return "📊 暂无有效的流水记录"

        # 统计
        total_income = sum(t["transaction_account"] for t in valid_transactions if t["type"] == 2)
        total_expense = sum(t["transaction_account"] for t in valid_transactions if t["type"] == 1)
        balance = total_income - total_expense

        income_count = len([t for t in valid_transactions if t["type"] == 2])
        expense_count = len([t for t in valid_transactions if t["type"] == 1])

        # 最大单笔支出
        expenses = [t for t in valid_transactions if t["type"] == 1]
        max_expense = max(expenses, key=lambda x: x["transaction_account"]) if expenses else None

        output = f"📊 用户流水汇总（最近{days}天）\n\n"
        output += f"💰 总收入：{total_income:.2f}元 ({income_count}笔)\n"
        output += f"💸 总支出：{total_expense:.2f}元 ({expense_count}笔)\n"
        output += f"💳 净收支：{balance:+.2f}元\n\n"

        if max_expense:
            output += f"🔥 最大单笔支出：{max_expense['transaction_name']} {max_expense['transaction_account']}元\n"

        output += f"📝 总记录数：{len(valid_transactions)}条\n"

        return output

    except Exception as e:
        return f"❌ 获取汇总信息时发生错误：{str(e)}"


@mcp.tool()
async def test_dont_user_id(user_id: int) -> str:
    """
    测试不传入user_id的情况

    Args:
        user_id: 用户ID（由AI服务传入）

    Returns:
        测试结果
    """
    return "你好"


if __name__ == "__main__":
    print("🚀 TransactionMCP 服务启动（使用假数据）")
    print("📊 支持的工具：")
    print("  - add_transaction: 添加流水记录")
    print("  - query_transactions: 查询流水记录")
    print("  - update_transaction: 更新流水记录")
    print("  - delete_transaction: 删除流水记录")
    print("  - get_user_summary: 获取用户汇总")
    print()
    mcp.run(transport="http", host="0.0.0.0", port=8001)
