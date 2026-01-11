# backend/main.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# 引入之前的爬虫和知识库
from crawler import get_real_time_trends 
# 👇 务必导入 STYLE_SAMPLES
from knowledge_base import STYLE_KNOWLEDGE_BASE, TITLE_PROMPT, CONTENT_PROMPT, STYLE_SAMPLES
from knowledge_base import TRENDING_TOPICS as FALLBACK_TRENDS 
from utils import parse_file_content
import traceback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_MAP = {
    "DeepSeek V3 (科研分析)": "deepseek-v3",
    "Qwen Max (创意写作)": "qwen-max", 
    "Qwen Plus (逻辑梳理)": "qwen-plus"
}

def get_llm(api_key, model_key, temperature):
    try:
        clean_key = api_key.strip()
        actual_model = MODEL_MAP.get(model_key, "deepseek-v3")
        print(f"🔧 [调试] LLM Init: {actual_model}, Temp={temperature}")
        return ChatOpenAI(
            api_key=clean_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=actual_model,
            temperature=temperature
        )
    except Exception as e:
        print(f"❌ LLM 初始化失败: {str(e)}")
        raise e

# --- 接口 1: 获取配置 ---
@app.get("/config")
async def get_config():
    print("🌍 正在获取热点数据...")
    real_trends = get_real_time_trends()
    
    if real_trends:
        print(f"✅ 爬虫成功，获取到 {len(real_trends)} 条热点")
        final_trends = real_trends
    else:
        print("⚠️ 爬虫未获取到数据，使用 Mock 数据兜底")
        final_trends = FALLBACK_TRENDS

    return {
        "styles": list(STYLE_KNOWLEDGE_BASE.keys()),
        "trends": final_trends,
        "models": list(MODEL_MAP.keys())
    }

# --- 接口 2: 生成标题 (改用 Form 接收文件) ---
@app.post("/generate_titles")
async def generate_titles(
    api_key: str = Form(...),
    subject: str = Form(...),
    style_key: str = Form(...),
    model_key: str = Form(...),
    creativity: float = Form(0.8),
    file: UploadFile = File(None) # 支持文件上传
):
    try:
        print(f"📩 [请求] 生成标题: 主题={subject}")
        
        # 1. 解析文件 (RAG)
        ref_summary = ""
        if file:
            content = await file.read()
            full_text = parse_file_content(content, file.filename)
            # 截取前1000字作为标题生成的参考摘要
            ref_summary = full_text[:1000]
            print(f"📄 文件已解析: {file.filename}, 提取摘要长度: {len(ref_summary)}")

        llm = get_llm(api_key, model_key, temperature=creativity)
        
        # 2. 获取风格和样本 (Few-Shot)
        style_guide = STYLE_KNOWLEDGE_BASE.get(style_key, "")
        # 👇 动态获取对应的样本，没找到就给空字符串
        examples = STYLE_SAMPLES.get(style_key, "无特定参考范文")

        # 3. 处理热点
        trends_text = "\n".join([f"- {t}" for t in FALLBACK_TRENDS])
        from crawler import CACHE_DATA
        if CACHE_DATA["trends"]:
             trends_text = "\n".join([f"- {t}" for t in CACHE_DATA["trends"]])

        prompt = ChatPromptTemplate.from_template(TITLE_PROMPT)
        chain = prompt | llm
        
        response = chain.invoke({
            "trends": trends_text, 
            "style": style_guide, 
            "subject": subject,
            "reference_summary": ref_summary,
            "examples": examples # 👈 传入样本
        })
        return {"titles": response.content}

    except Exception as e:
        print("\n❌ [严重错误] 生成标题失败:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"后端报错: {str(e)}")

# --- 接口 3: 生成内容 (改用 Form 接收文件) ---
@app.post("/generate_content")
async def generate_content(
    api_key: str = Form(...),
    title: str = Form(...),
    content_type: str = Form(...),
    style_key: str = Form(...),
    model_key: str = Form(...),
    video_length: float = Form(1.0),
    creativity: float = Form(0.5),
    file: UploadFile = File(None) # 支持文件上传
):
    try:
        print(f"📩 [请求] 生成内容: {title}")
        
        # 1. 解析文件 (RAG)
        ref_material = "无参考资料，请基于通用知识创作。"
        if file:
            content = await file.read()
            ref_material = parse_file_content(content, file.filename)
            print(f"📄 RAG文件注入成功，长度: {len(ref_material)}")
        
        llm = get_llm(api_key, model_key, temperature=creativity)
        
        # 2. 获取风格和样本
        style_guide = STYLE_KNOWLEDGE_BASE.get(style_key, "")
        examples = STYLE_SAMPLES.get(style_key, "无特定参考范文") # 👈 获取样本
        
        prompt = ChatPromptTemplate.from_template(CONTENT_PROMPT)
        chain = prompt | llm
        
        response = chain.invoke({
            "type": content_type,
            "title": title,
            "style": style_guide,
            "duration": video_length,
            "reference_material": ref_material,
            "examples": examples # 👈 传入样本
        })
        return {"content": response.content}

    except Exception as e:
        print("\n❌ [严重错误] 生成内容失败:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"后端报错: {str(e)}")