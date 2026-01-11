# backend/utils.py
import io
from docx import Document
from pypdf import PdfReader

def parse_file_content(file_bytes, filename):
    """
    解析上传的文件内容 (Word/PDF/TXT)
    返回: 提取出的文本字符串
    """
    text = ""
    try:
        if filename.endswith(".docx"):
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
        
        elif filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        elif filename.endswith(".txt"):
            text = file_bytes.decode("utf-8")
            
        else:
            return "不支持的文件格式，仅支持 .docx, .pdf, .txt"
            
    except Exception as e:
        return f"文件解析失败: {str(e)}"
    
    # 简单截断，防止Token爆炸 (视模型能力而定，DeepSeekV3支持长文本，可以留长一点)
    return text[:20000]