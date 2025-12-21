import asyncio
from typing import Optional, List
from pydantic import BaseModel, Field
from utils.OpenAIClientGenerator import OpenAIClientGenerator

system_prompt= [
    {
        "role": "system",
        "content": """
        角色：你是一个图像理解与识别工具。
        你的使命：请全面而详细地描述用户提供的图片的内容。
            按以下结构组织你的描述：
            主要内容:
            - 图片的核心主体是什么，在做什么
            场景与环境:
            - 拍摄地点、背景、周围环境
            - 时间线索（白天/夜晚/季节等）  
            视觉细节:
            - 颜色、光线、构图
            - 值得注意的细节元素
            整体印象:
            - 这张图片给人的感觉
        """
    }
]


# 定义结构化输出的数据模型
class ImageDescription(BaseModel):
    """图片描述的结构化模型"""
    image_index: int = Field(..., description="图片位置，从1开始")
    image_description_detail: str = Field(..., description="图片的详细描述")


class MultiImageDescription(BaseModel):
    """多图描述的结构化模型"""
    images: List[ImageDescription] = Field(..., description="图片的详细描述")
    summary: Optional[str] = Field(..., description="全部图片的摘要描述")



class ImageService:
    """图片服务"""

    def __init__(self):
        self.ai_client = None
        self.init_ai_client()

    def init_ai_client(self):
        """初始化AI客户端"""
        print("初始化OpenAI客户端...")
        self.ai_client = OpenAIClientGenerator().get_sync_client()

    async def visual_understanding(
            self,
            image_urls: list[str],
            prompt: str = "请详细描述这张图片的内容",
            model: str = "gpt-4.1"
    ):
        """
        图片理解与识别

        :param image_urls: 图片URL列表（支持多张图片）
        :param prompt: 提示词，指导AI如何分析图片
        :param model: 使用的模型，默认 gpt-4o（支持视觉）
        :return: AI对图片的描述
        """

        try:
            # 构建消息内容
            content = [
                {"type": "text", "text": prompt}
            ]

            # 添加所有图片
            for image_url in image_urls:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })

            # 调用OpenAI API
            response = self.ai_client.chat.completions.parse(
                model=model,
                messages=[
                    {
                        "role": system_prompt[0]["role"],
                        "content": system_prompt[0]["content"]
                    },
                    {
                    "role": "user",
                    "content": content
                    }
                ],
                response_format=MultiImageDescription,
                max_tokens=10000,

            )

            # 提取响应文本
            result: MultiImageDescription = response.choices[0].message.parsed
            print(result.summary)
            for description in result.images:
                print(f"图片{description.image_index}描述：{description.image_description_detail}")
            return result

        except Exception as e:
            print(f"图片理解与识别失败：{e}")


async def example_basic():
    service = ImageService()

    result = await service.visual_understanding(
        image_urls=["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPq1dP1m4_7I-yGmGHxnyMmtgVLE9EB_PUiQ&s","https://rimage.gnst.jp/livejapan.com/public/article/detail/a/00/00/a0000276/img/basic/a0000276_main.jpg","https://blog.amazingtalker.com/wp-content/uploads/2022/09/%E4%BB%A3%E5%85%A5%E6%B6%88%E5%8E%BB%E6%B3%95.png","https://lh6.googleusercontent.com/proxy/jZpHHsKAzGVYVpewNjQdQXGUleWmJJVN1KkqvyJB-h4BiN9TDeF45a-NB5noaa6nz9vSkGWtf9VW-swBCZC_22CfH3qSHBQ"]
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(example_basic())