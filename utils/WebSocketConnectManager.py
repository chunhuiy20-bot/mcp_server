from fastapi import WebSocket
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

"""
    创建全局唯一实例
    用于对连接的websocket做管理，方便信息的分发和接收
"""


class WebSocketManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 存储 unique_id 到 WebSocket 连接的映射
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, unique_id: str):
        """建立连接"""
        await websocket.accept()

        # 如果标识符已有连接，先断开旧连接
        if unique_id in self.connections:
            try:
                await self.connections[unique_id].close()
            except Exception as e:
                logger.warning(f"关闭旧连接时出错 unique_id={unique_id}: {e}")

        # 存储新连接
        self.connections[unique_id] = websocket
        logger.info(f"标识符 {unique_id} 已连接，当前连接数: {len(self.connections)}")

    def disconnect(self, unique_id: str):
        """断开连接"""
        if unique_id in self.connections:
            del self.connections[unique_id]
            logger.info(f"标识符 {unique_id} 已断开连接，当前连接数: {len(self.connections)}")

    def get_connection(self, unique_id: str) -> Optional[WebSocket]:
        """根据 unique_id 获取 WebSocket 连接"""
        return self.connections.get(unique_id)

    async def send_personal_message(self, message: str, unique_id: str) -> bool:
        """向指定标识符发送消息"""
        websocket = self.get_connection(unique_id)
        if websocket:
            try:
                await websocket.send_text(message)
                return True
            except Exception as e:
                logger.error(f"向标识符 {unique_id} 发送消息失败: {e}")
                # 发送失败时清理连接
                self.disconnect(unique_id)
                return False
        return False

    async def send_personal_json(self, data: dict, unique_id: str) -> bool:
        """向指定标识符发送 JSON 消息"""
        websocket = self.get_connection(unique_id)
        if websocket:
            try:
                await websocket.send_json(data)
                return True
            except Exception as e:
                logger.error(f"向标识符 {unique_id} 发送 JSON 消息失败: {e}")
                # 发送失败时清理连接
                self.disconnect(unique_id)
                return False
        return False

    async def broadcast_message(self, message: str):
        """向所有连接的用户广播消息"""
        if not self.connections:
            return

        # 记录需要清理的断开连接
        disconnected_ids = []

        for unique_id, websocket in self.connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"向标识符 {unique_id} 广播消息失败: {e}")
                disconnected_ids.append(unique_id)

        # 清理断开的连接
        for unique_id in disconnected_ids:
            self.disconnect(unique_id)

    async def broadcast_json(self, data: dict):
        """向所有连接的用户广播 JSON 消息"""
        if not self.connections:
            return

        # 记录需要清理的断开连接
        disconnected_ids = []

        for unique_id, websocket in self.connections.items():
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"向标识符 {unique_id} 广播 JSON 消息失败: {e}")
                disconnected_ids.append(unique_id)

        # 清理断开的连接
        for unique_id in disconnected_ids:
            self.disconnect(unique_id)

    def get_connected_users(self) -> list[str]:
        """获取所有在线用户的标识符列表"""
        return list(self.connections.keys())

    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.connections)

    def is_user_connected(self, unique_id: str) -> bool:
        """检查标识符是否在线"""
        return unique_id in self.connections

    # 新增方法：按前缀查找连接
    def get_connections_by_prefix(self, prefix: str) -> Dict[str, WebSocket]:
        """根据前缀获取连接（例如获取某个设备的所有连接）"""
        return {
            unique_id: websocket
            for unique_id, websocket in self.connections.items()
            if unique_id.startswith(prefix)
        }

    async def broadcast_to_prefix(self, message: str, prefix: str):
        """向指定前缀的所有连接广播消息"""
        target_connections = self.get_connections_by_prefix(prefix)

        if not target_connections:
            return

        disconnected_ids = []

        for unique_id, websocket in target_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"向标识符 {unique_id} 广播消息失败: {e}")
                disconnected_ids.append(unique_id)

        # 清理断开的连接
        for unique_id in disconnected_ids:
            self.disconnect(unique_id)

    async def broadcast_json_to_prefix(self, data: dict, prefix: str):
        """向指定前缀的所有连接广播 JSON 消息"""
        target_connections = self.get_connections_by_prefix(prefix)

        if not target_connections:
            return

        disconnected_ids = []

        for unique_id, websocket in target_connections.items():
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"向标识符 {unique_id} 广播 JSON 消息失败: {e}")
                disconnected_ids.append(unique_id)

        # 清理断开的连接
        for unique_id in disconnected_ids:
            self.disconnect(unique_id)


# 全局 WebSocket 管理器实例
ws_manager = WebSocketManager()