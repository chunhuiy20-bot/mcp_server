from typing import Dict, Tuple, Optional
from datetime import datetime
from threading import Lock


class AgentManager:
    """
    全局Agent服务管理器 - 单例模式
    使用 (user_id, conversation_id) 作为唯一索引
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            # 存储结构: {(user_id, conversation_id): {"agent": agent_instance, "last_access": datetime, "config": config}}
            self._agents: Dict[Tuple[int, int], dict] = {}
            self._lock = Lock()
            # 可选：设置过期时间，自动清理长时间未使用的agent
            self._expire_minutes = 120  # 30分钟未使用则过期
            self._initialized = True

    def get_agent(self, user_id: int, conversation_id: int) -> Optional['ReActAgentServiceImpl']:
        """
        获取Agent服务实例
        :param user_id: 用户ID
        :param conversation_id: 会话ID
        :return: Agent实例或None
        """
        key = (user_id, conversation_id)
        with self._lock:
            if key in self._agents:
                agent_info = self._agents[key]
                # 更新最后访问时间
                agent_info['last_access'] = datetime.now()
                return agent_info['agent']
        return None

    def set_agent(self, user_id: int, conversation_id: int, agent: 'ReActAgentServiceImpl', config: 'AgentConfig') -> None:
        """
        设置/缓存Agent服务实例
        :param user_id: 用户ID
        :param conversation_id: 会话ID
        :param agent: Agent实例
        :param config: Agent配置
        """
        key = (user_id, conversation_id)
        with self._lock:
            self._agents[key] = {
                'agent': agent,
                'config': config,
                'last_access': datetime.now(),
                'created_at': datetime.now()
            }

    def remove_agent(self, user_id: int, conversation_id: int) -> bool:
        """
        移除指定的Agent实例
        :param user_id: 用户ID
        :param conversation_id: 会话ID
        :return: 是否成功移除
        """
        print(f"移除用户 {user_id} 的会话 {conversation_id} 的代理实例")
        key = (user_id, conversation_id)
        with self._lock:
            if key in self._agents:
                del self._agents[key]
                return True
        return False

    def clear_expired_agents(self) -> int:
        """
        清理过期的Agent实例
        :return: 清理的数量
        """
        now = datetime.now()
        expired_keys = []

        with self._lock:
            for key, agent_info in self._agents.items():
                if (now - agent_info['last_access']).total_seconds() > self._expire_minutes * 60:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._agents[key]
        print(f"清理了 {len(expired_keys)} 个过期的代理实例")
        return len(expired_keys)

    def get_stats(self) -> dict:
        """
        获取管理器统计信息
        :return: 统计数据
        """
        with self._lock:
            return {
                'total_agents': len(self._agents),
                'agents': [
                    {
                        'user_id': key[0],
                        'conversation_id': key[1],
                        'last_access': info['last_access'],
                        'created_at': info['created_at']
                    }
                    for key, info in self._agents.items()
                ]
            }

    def clear_all(self) -> None:
        """清空所有Agent实例"""
        with self._lock:
            self._agents.clear()


# 创建全局单例实例
agent_manager = AgentManager()
