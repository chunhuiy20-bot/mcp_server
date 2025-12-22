import os

from utils.OpenAIClientGenerator import OpenAIClientGenerator
from openai import OpenAI
#
# client: OpenAI = OpenAIClientGenerator().get_sync_client()
# audio_file = open("simple_speech.mp3", "rb")
# print(type(audio_file) == bytes)
#
# transcription = client.audio.transcriptions.create(
#     model="gpt-4o-transcribe",
#     file=audio_file,
#     response_format="text"
# )
#
# print(transcription)


# import base64
# from openai import OpenAI
#
# client: OpenAI = OpenAIClientGenerator().get_sync_client()
#
# def to_data_url(path: str) -> str:
#     with open(path, "rb") as fh:
#         return "data:audio/wav;base64," + base64.b64encode(fh.read()).decode("utf-8")
#
# with open("simple_speech.mp3", "rb") as audio_file:
#     transcript = client.audio.transcriptions.create(
#         model="gpt-4o-transcribe",
#         file=audio_file,
#         response_format="diarized_json",
#         chunking_strategy="auto",
#         extra_body={
#             "known_speaker_names": ["agent"],
#             "known_speaker_references": [to_data_url("simple_speech.mp3")],
#         },
#     )
#
# for segment in transcript.segments:
#     print(segment.speaker, segment.text, segment.start, segment.end)


from PIL import Image, ImageDraw
from openai import OpenAI
client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL2"), api_key=os.getenv("OPENAI_API_KEY2"))
# #
# 编辑图片 - 需要原图和遮罩
response = client.images.edit(
    model="dall-e-2",  # 只有 dall-e-2 支持编辑
    image=open("original_rgba.png", "rb"),
    mask=open("mask.png", "rb"),  # 白色区域会被编辑，黑色区域保持不变
    prompt="A realistic fresh sandwich placed naturally in the masked area, with soft bread, visible layers of lettuce, tomato, cheese, and sliced meat. The sandwich should match the lighting, perspective, and style of the original image, with natural shadows and high detail, looking photorealistic and appetizing.",
    n=1
)
print(response)
image_url = response.data[0].url
print(image_url)


# 遮罩创建
# from PIL import Image, ImageDraw
# import numpy as np
#
#
# def create_circle_mask(image_path, center, radius):
#     """创建圆形遮罩"""
#     # 打开原图获取尺寸
#     original = Image.open(image_path)
#     width, height = original.size
#
#     # 创建黑色背景
#     mask = Image.new('RGB', (width, height), 'black')
#     draw = ImageDraw.Draw(mask)
#
#     # 画白色圆形（要编辑的区域）
#     left = center[0] - radius
#     top = center[1] - radius
#     right = center[0] + radius
#     bottom = center[1] + radius
#
#     draw.ellipse([left, top, right, bottom], fill='white')
#
#     mask.save('mask.png')
#     return 'mask.png'
#
#
# def create_rectangle_mask(image_path, x, y, width, height):
#     """创建矩形遮罩"""
#     original = Image.open(image_path)
#     img_width, img_height = original.size
#
#     mask = Image.new('RGB', (img_width, img_height), 'black')
#     draw = ImageDraw.Draw(mask)
#
#     # 画白色矩形
#     draw.rectangle([x, y, x + width, y + height], fill='white')
#
#     mask.save('mask.png')
#     return 'mask.png'
#
#
# # 使用示例
# # create_circle_mask('original.png', center=(512, 512), radius=200)
# create_rectangle_mask('original.png', x=350, y=780, width=400, height=300)

#
#
# import base64
# def convert_to_rgba(image_path):
#     """将图片转换为 RGBA 格式"""
#     img = Image.open(image_path)
#
#     # 转换为 RGBA
#     if img.mode != 'RGBA':
#         img = img.convert('RGBA')
#
#     # 保存为新文件
#     rgba_path = image_path.replace('.png', '_rgba.png').replace('.jpg', '_rgba.png')
#     img.save(rgba_path, 'PNG')
#
#     return rgba_path
#
#
# def create_rgba_mask(image_path, mask_area):
#     """创建 RGBA 格式的遮罩"""
#     original = Image.open(image_path)
#     width, height = original.size
#
#     # 创建 RGBA 遮罩（黑色背景，透明度为255）
#     mask = Image.new('RGBA', (width, height), (0, 0, 0, 255))
#     draw = ImageDraw.Draw(mask)
#
#     if mask_area['type'] == 'circle':
#         center = mask_area['center']
#         radius = mask_area['radius']
#         left = center[0] - radius
#         top = center[1] - radius
#         right = center[0] + radius
#         bottom = center[1] + radius
#         # 白色区域，完全不透明
#         draw.ellipse([left, top, right, bottom], fill=(255, 255, 255, 255))
#
#     elif mask_area['type'] == 'rect':
#         x, y = mask_area['x'], mask_area['y']
#         w, h = mask_area['width'], mask_area['height']
#         draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255, 255))
#
#     mask_path = 'temp_mask_rgba.png'
#     mask.save(mask_path, 'PNG')
#
#     return mask_path
#
#
# def edit_image_fixed(image_path, mask_area, edit_prompt):
#     """
#     修复后的图片编辑函数
#     """
#     try:
#         # 1. 转换原图为 RGBA
#         rgba_image_path = convert_to_rgba(image_path)
#         print(f"原图转换为 RGBA: {rgba_image_path}")
#
#         # 2. 创建 RGBA 遮罩
#         mask_path = create_rgba_mask(rgba_image_path, mask_area)
#         print(f"遮罩创建完成: {mask_path}")
#
#         # 3. 验证图片格式
#         img = Image.open(rgba_image_path)
#         mask_img = Image.open(mask_path)
#         print(f"原图格式: {img.mode}, 尺寸: {img.size}")
#         print(f"遮罩格式: {mask_img.mode}, 尺寸: {mask_img.size}")
#
#         # 4. 调用 OpenAI API
#         response = client.images.edit(
#             model="dall-e-2",
#             image=open(rgba_image_path, "rb"),
#             mask=open(mask_path, "rb"),
#             prompt=edit_prompt,
#             n=1,
#             # response_format="b64_json"
#         )
#         print("API 响应:", response)
#
#         # 5. 保存结果
#         # image_data = base64.b64decode(response.data[0].b64_json)
#         # output_path = f"edited_{edit_prompt.replace(' ', '_')[:20]}.png"
#         #
#         # with open(output_path, "wb") as f:
#         #     f.write(image_data)
#         #
#         # print(f"✅ 编辑完成: {output_path}")
#         # return output_path
#
#     except Exception as e:
#         print(f"❌ 编辑失败: {e}")
#         return None
#
#
# # 使用示例
# if __name__ == "__main__":
#     # 编辑图片中心区域
#     result = edit_image_fixed(
#         image_path="original.png",  # 你的图片路径
#         mask_area={
#             'type': 'circle',
#             'center': (500, 500),
#             'radius': 150
#         },
#         edit_prompt="生成一个三明治"
#     )
#
#     if result:
#         print(f"编辑成功，输出文件: {result}")


# from PIL import Image, ImageDraw
#
#
# def create_correct_mask(image_path, edit_area):
#     """
#     创建正确的遮罩 - 透明区域会被编辑
#
#     Args:
#         image_path: 原图路径
#         edit_area: 编辑区域 {'type': 'rect', 'x': x, 'y': y, 'width': w, 'height': h}
#     """
#
#     original = Image.open(image_path)
#     width, height = original.size
#
#     # 创建完全不透明的遮罩（保持原图的区域）
#     mask = Image.new('RGBA', (width, height), (0, 0, 0, 255))  # 黑色，完全不透明
#
#     draw = ImageDraw.Draw(mask)
#
#     if edit_area['type'] == 'rect':
#         x, y = edit_area['x'], edit_area['y']
#         w, h = edit_area['width'], edit_area['height']
#
#         # 在要编辑的区域画透明矩形（alpha=0）
#         draw.rectangle([x, y, x + w, y + h], fill=(0, 0, 0, 0))  # 完全透明
#
#     elif edit_area['type'] == 'circle':
#         center = edit_area['center']
#         radius = edit_area['radius']
#         left = center[0] - radius
#         top = center[1] - radius
#         right = center[0] + radius
#         bottom = center[1] + radius
#
#         # 在要编辑的区域画透明圆形（alpha=0）
#         draw.ellipse([left, top, right, bottom], fill=(0, 0, 0, 0))  # 完全透明
#
#     mask_path = 'correct_mask.png'
#     mask.save(mask_path, 'PNG')
#
#     print(f"✅ 正确遮罩已创建: {mask_path}")
#     return mask_path
#
#
# def visualize_mask(image_path, mask_path):
#     """可视化遮罩效果"""
#
#     original = Image.open(image_path)
#     mask = Image.open(mask_path)
#
#     # 创建预览：透明区域显示为红色
#     preview = original.copy().convert('RGBA')
#
#     # 获取遮罩的 alpha 通道
#     mask_alpha = mask.split()[-1]  # 获取 alpha 通道
#
#     # 创建红色覆盖层
#     red_overlay = Image.new('RGBA', original.size, (255, 0, 0, 128))
#
#     # 在透明区域（alpha=0）显示红色
#     for x in range(original.width):
#         for y in range(original.height):
#             if mask_alpha.getpixel((x, y)) == 0:  # 透明区域
#                 preview.putpixel((x, y), (255, 0, 0, 255))  # 红色标记
#
#     preview.save('mask_preview.png')
#     print("✅ 遮罩预览已保存: mask_preview.png (红色区域将被编辑)")
#
#
# # 正确的使用方法
# def correct_image_edit():
#     """正确的图片编辑流程"""
#
#     from openai import OpenAI
#     import requests
#
#     client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL2"), api_key=os.getenv("OPENAI_API_KEY2"))
#
#     # 1. 确保原图是 RGBA 格式
#     original = Image.open("original.png").convert('RGBA')
#     original.save('original_rgba.png', 'PNG')
#
#     # 2. 创建正确的遮罩（透明区域 = 编辑区域）
#     mask_path = create_correct_mask('original_rgba.png', {
#         'type': 'rect',
#         'x': 300,
#         'y': 400,
#         'width': 300,
#         'height': 200
#     })
#
#     # 3. 可视化遮罩
#     visualize_mask('original_rgba.png', mask_path)
#
#     # 4. 调用编辑 API
#     try:
#         response = client.images.edit(
#             model="dall-e-2",
#             image=open("original_rgba.png", "rb"),
#             mask=open(mask_path, "rb"),
#             prompt="a delicious sandwich with lettuce, tomato, and ham on a white plate",
#             n=1,
#             size="1024x1024"
#         )
#
#         print("✅ 编辑成功!")
#         print(f"🔗 结果: {response.data[0].url}")
#
#         # 下载结果
#         img_response = requests.get(response.data[0].url)
#         with open('edited_result.png', 'wb') as f:
#             f.write(img_response.content)
#         print("✅ 结果已保存: edited_result.png")
#
#         return response.data[0].url
#
#     except Exception as e:
#         print(f"❌ 编辑失败: {e}")
#         return None
#
#
# # 运行正确的编辑
# correct_image_edit()
