from typing import Union, BinaryIO
import requests
from agent.ai_chat.io_strategy.input_strategy.InputStrategy import InputStrategy
from schemas.common.Result import Result
from utils.OpenAIClientGenerator import OpenAIClientGenerator
from io import BytesIO


class VoiceInputStrategy(InputStrategy):
    """语音输入策略"""

    def __init__(self):
        self.client = OpenAIClientGenerator().get_async_client()

    async def process(self, data: bytes, **kwargs) -> Result[str]:
        """
        处理语音数据

        Args:
            data: 音频字节数据 (bytes 类型)
            **kwargs: 可选参数

        Returns:
            识别后的文本
        """
        print("语音识别中...")
        result = await self._speech_to_text(data, **kwargs)
        print(f"识别结果: {result}")
        return result

    # noinspection PyMethodMayBeStatic
    async def _speech_to_text(self, audio: bytes, **kwargs):
        """
        调用语音识别API
        Args:
            audio: 音频字节数据 (bytes 类型)
            也可以是voice_url
        """
        if voice_url := kwargs.get('voice_url'):
            result = await self._download_voice_file(voice_url)
            if result.code != 200:
                return result
            else:
                return await self._call_whisper(result.data, **kwargs)
        elif audio is not None and isinstance(audio, bytes):
            print("使用 audio：", audio[:10])
            # 将 bytes 转换为文件对象  bytes -> BytesIO 对象
            audio_file = BytesIO(audio)
            audio_file.name = kwargs.get('filename', 'audio.mp3')
            return await self._call_whisper(audio_file, **kwargs)
        else:
            raise ValueError("请提供有效的音频数据")

    # noinspection PyMethodMayBeStatic
    async def _call_whisper(self, audio_file: Union[BytesIO, BinaryIO], **kwargs) -> Result[str]:
        """
        调用语音识别API
        Args:
            audio: 音频字节数据 (bytes 类型)
            也可以是voice_url
        """
        try:
            transcription_params = {
                "model": kwargs.get('model', 'whisper-1'),
                "file": audio_file,  # 传入 BytesIO 对象（不是 bytes）
                "response_format": kwargs.get('response_format', 'text')
            }
            # 添加可选参数
            if 'language' in kwargs:
                transcription_params["language"] = kwargs['language']
            if 'prompt' in kwargs:
                transcription_params["prompt"] = kwargs['prompt']
            # transcription = self.client.audio.transcriptions.create(**transcription_params)
            print(f"请求参数: {transcription_params}")
            transcription = await self.client.audio.transcriptions.create(**transcription_params)
            return Result(data=transcription)
        except Exception as e:
            return Result(code=500, message=str(e))


    async def _download_voice_file(self, voice_url: str) -> Result[BytesIO]:
        """
        从 URL 下载音频并转录
        Args:
            voice_url: 音频文件 URL
        Returns:
            转录结果
        """
        try:
            print(f"开始从 URL 下载音频: {voice_url}")

            # 下载音频文件
            response = requests.get(voice_url, timeout=60)
            response.raise_for_status()

            print(f"音频下载完成，大小: {len(response.content)} 字节")

            # 检查文件大小（OpenAI 限制 25MB）
            if len(response.content) > 25 * 1024 * 1024:
                return Result(code=400, message="音频文件过大，超过 25MB 限制")

            # 转换为 BytesIO 对象
            audio_file = BytesIO(response.content)

            # 从 URL 推断文件扩展名
            file_extension = self._get_file_extension_from_url(voice_url)
            audio_file.name = f"audio{file_extension}"

            # 返回文件对象
            return Result(data=audio_file)

        except Exception as e:
            return Result(code=500, message=str(e))

    # noinspection PyMethodMayBeStatic
    def _get_file_extension_from_url(self, url: str) -> str:
        """
        从 URL 获取文件扩展名

        Args:
            url: 文件 URL

        Returns:
            文件扩展名
        """
        try:
            # 移除查询参数
            clean_url = url.split('?')[0]

            if '.' in clean_url:
                extension = '.' + clean_url.split('.')[-1].lower()

                # OpenAI 支持的音频格式
                supported_formats = ['.mp3', '.mp4', '.mpeg', '.m4a', '.wav', '.webm']

                if extension in supported_formats:
                    return extension
            # 默认返回 .mp3
            return '.mp3'

        except Exception as e:
            print(f"处理 URL 时发生错误: {str(e)},返回 .mp3 作为兜底")
            return '.mp3'


# # 测试不同的输入类型
# async def test_types():
#     strategy: InputStrategy = VoiceInputStrategy()
#
#     # 1. 正确的输入：bytes
#     with open("simple_speech.mp3", "rb") as f:
#         audio_bytes = f.read()  # 这是 bytes 类型
#
#     print("=== 测试 bytes 输入 ===")
#     result = await strategy.process(data=None, voice_url="https://hdd-ai-image.oss-cn-beijing.aliyuncs.com/local_temp_documents/simple_speech.mp3")  # 正确
#
#
#
# if __name__ == "__main__":
#     import asyncio
#
#     asyncio.run(test_types())
