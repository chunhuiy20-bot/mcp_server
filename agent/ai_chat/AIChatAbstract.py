from abc import ABC, abstractmethod


class AIChatAbstract(ABC):
    """
    AI聊天接口,无论什么智能体模式，本质上都是在和ai进行对话
    所以这个是最底层的抽象
    """

    @abstractmethod
    async def chat(self, user_input: str, **kwargs):
        """
        聊天方法
        :param user_input:
        :param kwargs: 其他参数
        :return: 聊天结果
        """
        pass

    @abstractmethod
    async def chat_stream(self, user_input: str, **kwargs):
        """
        流式聊天方法
        :param user_input:
        :param kwargs: 其他参数
        :return: 聊天结果
        """
        pass