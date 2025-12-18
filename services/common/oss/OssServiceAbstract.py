from abc import ABC
from typing import Optional

from schemas.common.Result import Result


class OssServiceAbstract(ABC):
    """
    Abstract class for OSS handler. 对象存储服务抽象操作类
    """


    async def upload_file(self, file_path: str, object_name: Optional[str] = 'local_temp_documents/', bucket_name: Optional[str] = "tx-factory") -> Result:
        """
        上传文件
        :param file_path:
        :param bucket_name:
        :param object_name:
        :return:
        """
        pass
