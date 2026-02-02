from openai import OpenAI

client = OpenAI(api_key="806f4c5f188d46d3a20a1662a4224c81", base_url="https://api.lingyiwanwu.com/v1")  # 自动读取 OPENAI_API_KEY

response = client.chat.completions.create(
    model="yi-vision-v2",  # 测试用，便宜、快、稳定
    messages=[
        {"role": "system", "content": "你是一个测试助手"},
        {"role": "user", "content": "你是基于那个大模型的？"}
    ]
)
print(response)
print(response.choices[0].message.content)
