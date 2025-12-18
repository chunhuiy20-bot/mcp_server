import os
import asyncio
import uuid
from pathlib import Path
from typing import Optional
import aiohttp
import oss2
from dotenv import load_dotenv
from oss2.exceptions import OssError
from schemas.common.Result import Result
from services.common.oss.OssServiceAbstract import OssServiceAbstract
load_dotenv()


class AliyunOssService(OssServiceAbstract):
    """
    阿里云OSS处理器实现类
    """

    def __init__(self, access_key_id: Optional[str] = None, access_key_secret: Optional[str] = None,
                 endpoint: Optional[str] = None):
        """
        初始化阿里云OSS客户端
        :param access_key_id: 阿里云AccessKey ID，为空时从环境变量ALIYUN_OSS_ACCESS_KEY_ID获取
        :param access_key_secret: 阿里云AccessKey Secret，为空时从环境变量ALIYUN_OSS_ACCESS_KEY_SECRET获取
        :param endpoint: OSS访问域名，为空时从环境变量ALIYUN_OSS_ENDPOINT获取
        """
        # 从.env文件或环境变量中获取配置
        self.access_key_id = access_key_id or os.getenv('ALIYUN_AK_ID')
        self.access_key_secret = access_key_secret or os.getenv('ALIYUN_AK_SECRET')
        self.endpoint = endpoint or os.getenv('ALIYUN_OSS_ENDPOINT')

        # # 验证必需的配置是否存在
        if not self.access_key_id or not self.access_key_secret or not self.endpoint:
            raise ValueError("缺少必要的环境变量")

        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)

    def _get_bucket(self, bucket_name: Optional[str] = "hdd-ai-image") -> oss2.Bucket:
        """
        获取Bucket对象
        :param bucket_name: 存储桶名称
        :return: Bucket对象
        """
        return oss2.Bucket(self.auth, self.endpoint, bucket_name)

    async def upload_file(self, file_path: str, object_name: Optional[str] = 'local_temp_documents/', bucket_name: Optional[str] = "hdd-ai-image") -> Result:
        """
        上传文件到阿里云OSS
        :param file_path: 本地文件路径
        :param bucket_name: OSS存储桶名称
        :param object_name: OSS中的对象名称（文件路径）
        :return: 上传成功返回True，失败返回False
        """
        try:
            # 检查本地文件是否存在
            if not os.path.exists(file_path):
                print(f"本地文件不存在: {file_path}")
                return Result(code=404, message="文件不存在", data=None)

            # 在线程池中执行同步操作
            object_name = os.path.join(object_name, os.path.basename(file_path))

            def _upload():
                bucket = self._get_bucket(bucket_name)
                # 上传文件
                result = bucket.put_object_from_file(object_name, file_path)
                print(result)
                return result.status == 200
            # 使用asyncio在线程池中执行
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, _upload)

            if success:
                print(f"文件上传成功: {file_path} -> https://{bucket_name}.{self.endpoint}/{object_name}")
            else:
                return Result(code=500, message="文件上传失败", data=None)
            return Result(code=200, message="文件上传成功", data=f"https://{bucket_name}.{self.endpoint}/{object_name}")

        except OssError as e:
            print(f"OSS错误: {e}")
            return Result(code=500, message="上传失败", data=None)
        except Exception as e:
            print(f"上传文件时发生错误: {e}")
            return Result(code=500, message="上传失败", data=None)

    async def download_file_from_oss(self, object_name: Optional[str], file_path: Optional[str], bucket_name: Optional[str] = "tx-factory") -> bool:
        """
        从阿里云OSS下载文件
        :param bucket_name: OSS存储桶名称
        :param object_name: OSS中的对象名称（文件路径）
        :param file_path: 本地保存文件路径
        :return: 下载成功返回True，失败返回False
        """
        try:
            # 确保本地目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            def _download():
                bucket = self._get_bucket()
                # 检查对象是否存在
                if not bucket.object_exists(object_name):
                    print(f"OSS中文件不存在: {bucket_name}/{object_name}")
                    return False

                # 下载文件
                result = bucket.get_object_to_file(object_name, file_path)
                print(result)
                return True

            # 使用asyncio在线程池中执行
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, _download)

            if success:
                print(f"文件下载成功: {bucket_name}/{object_name} -> {file_path}")
            else:
                print(f"文件下载失败: {bucket_name}/{object_name}")

            return success

        except OssError as e:
            print(f"OSS错误: {e}")
            return False
        except Exception as e:
            print(f"下载文件时发生错误: {e}")
            return False

    async def read_file(self, object_name: str, bucket_name: Optional[str] = "tx-factory",
                        decode: bool = False) -> Result:
        """
        从阿里云OSS读取文件内容
        :param object_name: OSS中的对象名称（文件路径），可以是完整URL或对象路径
        :param bucket_name: OSS存储桶名称
        :param decode: 是否尝试解码为文本（仅适用于文本文件）
        :return: Result对象，成功时data包含文件内容(bytes或str)
        """
        try:
            print(f"正在读取文件: {object_name}")
            # 如果传入的是完整URL，提取object_name

            if object_name.startswith('http://') or object_name.startswith('https://'):
                # 解析URL，提取对象名称
                # 格式: https://bucket-name.endpoint/object-name
                url_parts = object_name.split('/')
                # 找到endpoint后的所有部分作为object_name
                object_name = '/'.join(url_parts[3:])

            def _read():
                bucket = self._get_bucket(bucket_name)

                # 检查对象是否存在
                if not bucket.object_exists(object_name):
                    print(f"OSS中文件不存在: {bucket_name}/{object_name}")
                    return None

                # 读取文件内容
                result = bucket.get_object(object_name)
                # 读取所有内容
                content = result.read()
                return content

            # 使用asyncio在线程池中执行
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, _read)

            if content is not None:
                print(f"文件读取成功: {bucket_name}/{object_name}, 大小: {len(content)} bytes")

                # 如果需要解码且是文本文件
                if decode:
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        # 如果UTF-8解码失败，尝试其他编码
                        try:
                            content = content.decode('gbk')
                        except UnicodeDecodeError:
                            print(f"警告: 无法解码文件，返回原始bytes")

                return Result(code=200, message="读取成功", data=content)
            else:
                return Result(code=404, message="文件不存在", data=None)

        except OssError as e:
            print(f"OSS错误: {e}")
            return Result(code=500, message=f"OSS错误: {str(e)}", data=None)
        except Exception as e:
            print(f"读取文件时发生错误: {e}")
            return Result(code=500, message=f"读取失败: {str(e)}", data=None)

    # noinspection PyMethodMayBeStatic
    async def download_image_to_local_temp(self, url: str, local_temp_dir: str = "local_temp_documents") -> Optional[str]:
        """下载图片到指定的本地临时目录"""

        # 1. 确定保存目录并创建 (如果不存在)
        # 使用 Pathlib 确保跨平台兼容性
        save_dir = Path(local_temp_dir)
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"创建目录失败: {save_dir} -> {str(e)}")
            return None

        try:
            timeout = aiohttp.ClientTimeout(total=180)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # 根据Content-Type确定文件后缀
                        content_type = response.headers.get('content-type', '').lower()
                        suffix = self._get_suffix_from_content_type(content_type)

                        # 2. 生成一个唯一的文件名
                        file_name = f"{uuid.uuid4()}{suffix}"
                        save_path = save_dir / file_name

                        # 3. 写入文件
                        content = await response.read()
                        save_path.write_bytes(content)

                        # 返回完整的保存路径字符串
                        return str(save_path)
                    else:
                        print(f"下载失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"下载图片异常: {str(e)}")
            return None

    # noinspection PyMethodMayBeStatic
    def _get_suffix_from_content_type(self, content_type: str) -> str:
        """根据Content-Type获取文件后缀"""
        content_type_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/bmp': '.bmp',
            'image/tiff': '.tiff',
            'image/svg+xml': '.svg',
            'image/x-icon': '.ico',
            'image/vnd.microsoft.icon': '.ico'
        }
        return content_type_map.get(content_type, '.png')


# 使用示例
async def main():
    pass

if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
