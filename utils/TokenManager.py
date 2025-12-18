import threading
from dotenv import load_dotenv
from datetime import datetime, timedelta
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import json
import os
load_dotenv()
"""
    TokenManager类
    由于阿里云的智能语音交互token不能长久使用，需要校验token有效期和刷新token
    所以创建TokenManager类用于管理token.
    其次，让TokenManager类单例，避免频繁刷新token
"""
class TokenManager:
    """Token管理器，负责获取和刷新Token（单例模式）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        初始化Token管理器（单例，只会初始化一次）
        自动从环境变量读取配置
        """
        # 避免重复初始化
        if self._initialized:
            return

        # 从环境变量读取配置
        self.ak_id = os.getenv('ALIYUN_AK_ID')
        self.ak_secret = os.getenv('ALIYUN_AK_SECRET')
        self.region = os.getenv('ALIYUN_REGION', 'cn-shanghai')

        if not self.ak_id or not self.ak_secret:
            raise ValueError(
                "环境变量 ALIYUN_AK_ID 和 ALIYUN_AK_SECRET 未设置！\n"
                "请在 .env 文件中配置：\n"
                "ALIYUN_AK_ID=your_access_key_id\n"
                "ALIYUN_AK_SECRET=your_access_key_secret"
            )

        self.token = None
        self.expire_time = None
        self._token_lock = threading.Lock()

        self._initialized = True
        print("✅ TokenManager 单例初始化成功")

    def get_token(self, force_refresh: bool = False) -> str:
        """
        获取Token，如果过期或不存在则自动刷新
        :param force_refresh: 是否强制刷新
        :return: Token字符串
        """
        with self._token_lock:
            if force_refresh or not self._is_token_valid():
                self._refresh_token()
            return self.token

    def _is_token_valid(self) -> bool:
        """检查Token是否有效（存在且未过期）"""
        if not self.token or not self.expire_time:
            return False

        buffer_time = timedelta(minutes=5)
        now = datetime.now()
        return now < (self.expire_time - buffer_time)

    def _refresh_token(self):
        """刷新Token"""
        try:
            client = AcsClient(
                self.ak_id,
                self.ak_secret,
                self.region
            )

            request = CommonRequest()
            request.set_method('POST')
            request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
            request.set_version('2019-02-28')
            request.set_action_name('CreateToken')

            response = client.do_action_with_exception(request)
            result = json.loads(response)

            if 'Token' in result and 'Id' in result['Token']:
                self.token = result['Token']['Id']
                expire_timestamp = result['Token']['ExpireTime']
                self.expire_time = datetime.fromtimestamp(expire_timestamp)
                print(f"🔄 Token刷新成功，token:f{self.token},过期时间: {self.expire_time}")
            else:
                raise Exception("Token响应格式错误")

        except Exception as e:
            print(f"❌ Token刷新失败: {e}")
            raise
