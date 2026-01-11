# backend/test_api.py
from langchain_openai import ChatOpenAI

# 填入你的 Key 测试
API_KEY = "sk-e98be4ae44e8493386ffb81121cd7cd9"  # 把你的Key粘贴在这里
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

print("正在尝试连接阿里云百炼...")

try:
    llm = ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model="deepseek-v3", # 确保你在百炼控制台开通了这个模型
        temperature=0.7
    )
    
    response = llm.invoke("你好，请回复'连接成功'四个字")
    print("✅ 测试成功！返回内容：", response.content)

except Exception as e:
    print("\n❌ 连接失败！错误详情如下：")
    print(e)