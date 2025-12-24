import os
from PIL import Image, ImageDraw


def create_correct_mask(image_path, edit_area):
    """
    创建正确的遮罩 - 透明区域会被编辑

    Args:
        image_path: 原图路径
        edit_area: 编辑区域 {'type': 'rect', 'x': x, 'y': y, 'width': w, 'height': h}
    """

    original = Image.open(image_path)
    width, height = original.size

    # 创建完全不透明的遮罩（保持原图的区域）
    mask = Image.new('RGBA', (width, height), (0, 0, 0, 255))  # 黑色，完全不透明

    draw = ImageDraw.Draw(mask)

    if edit_area['type'] == 'rect':
        x, y = edit_area['x'], edit_area['y']
        w, h = edit_area['width'], edit_area['height']

        # 在要编辑的区域画透明矩形（alpha=0）
        draw.rectangle([x, y, x + w, y + h], fill=(0, 0, 0, 0))  # 完全透明

    elif edit_area['type'] == 'circle':
        center = edit_area['center']
        radius = edit_area['radius']
        left = center[0] - radius
        top = center[1] - radius
        right = center[0] + radius
        bottom = center[1] + radius

        # 在要编辑的区域画透明圆形（alpha=0）
        draw.ellipse([left, top, right, bottom], fill=(0, 0, 0, 0))  # 完全透明

    mask_path = 'correct_mask.png'
    mask.save(mask_path, 'PNG')

    print(f"✅ 正确遮罩已创建: {mask_path}")
    return mask_path


def visualize_mask(image_path, mask_path):
    """可视化遮罩效果"""

    original = Image.open(image_path)
    mask = Image.open(mask_path)

    # 创建预览：透明区域显示为红色
    preview = original.copy().convert('RGBA')

    # 获取遮罩的 alpha 通道
    mask_alpha = mask.split()[-1]  # 获取 alpha 通道

    # 创建红色覆盖层
    red_overlay = Image.new('RGBA', original.size, (255, 0, 0, 128))

    # 在透明区域（alpha=0）显示红色
    for x in range(original.width):
        for y in range(original.height):
            if mask_alpha.getpixel((x, y)) == 0:  # 透明区域
                preview.putpixel((x, y), (255, 0, 0, 255))  # 红色标记

    preview.save('mask_preview.png')
    print("✅ 遮罩预览已保存: mask_preview.png (红色区域将被编辑)")


# 正确的使用方法
def correct_image_edit():
    """正确的图片编辑流程"""

    from openai import OpenAI
    import requests

    client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL2"), api_key=os.getenv("OPENAI_API_KEY2"))

    # 1. 确保原图是 RGBA 格式
    original = Image.open("original.png").convert('RGBA')
    original.save('original_rgba.png', 'PNG')

    # 2. 创建正确的遮罩（透明区域 = 编辑区域）
    mask_path = create_correct_mask('original_rgba.png', {
        'type': 'rect',
        'x': 300,
        'y': 400,
        'width': 300,
        'height': 200
    })

    # 3. 可视化遮罩
    visualize_mask('original_rgba.png', mask_path)

    # 4. 调用编辑 API
    try:
        response = client.images.edit(
            model="dall-e-2",
            image=open("original_rgba.png", "rb"),
            mask=open(mask_path, "rb"),
            prompt="a delicious sandwich with lettuce, tomato, and ham on a white plate",
            n=1,
            size="1024x1024"
        )

        print("✅ 编辑成功!")
        print(f"🔗 结果: {response.data[0].url}")

        # 下载结果
        img_response = requests.get(response.data[0].url)
        with open('edited_result.png', 'wb') as f:
            f.write(img_response.content)
        print("✅ 结果已保存: edited_result.png")

        return response.data[0].url

    except Exception as e:
        print(f"❌ 编辑失败: {e}")
        return None


# 运行正确的编辑
correct_image_edit()


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