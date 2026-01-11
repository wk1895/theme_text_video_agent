# backend/crawler.py
import requests
from bs4 import BeautifulSoup
import time
import random

# --- 配置伪装头 (防止被网站拦截) ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_weibo_hot_search():
    """
    抓取微博热搜榜 (https://s.weibo.com/top/summary)
    """
    url = "https://s.weibo.com/top/summary"
    try:
        # 发送请求
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.encoding = 'utf-8' # 确保中文不乱码
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 微博热搜在 td class="td-02" 下的 a 标签里
        items = soup.select("td.td-02 > a")
        
        trends = []
        for item in items:
            title = item.get_text().strip()
            # 过滤掉一些广告或置顶的无效内容
            if not title or title == "javascript:void(0);":
                continue
            trends.append(f"【微博】{title}")
            
        # 只取前 10 条
        return trends[:10]
    
    except Exception as e:
        print(f"微博爬取失败: {e}")
        return []

def scrape_baidu_hot_search():
    """
    抓取百度热搜榜 (https://top.baidu.com/board?tab=realtime)
    """
    url = "https://top.baidu.com/board?tab=realtime"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 百度热搜标题通常在 class="c-single-text-ellipsis"
        items = soup.select(".c-single-text-ellipsis")
        
        trends = []
        for item in items:
            title = item.get_text().strip()
            if title:
                trends.append(f"【百度】{title}")
        
        return trends[:10]
    
    except Exception as e:
        print(f"百度爬取失败: {e}")
        return []

# --- 缓存机制 (非常重要！) ---
# 避免前端每次刷新都去爬一次（容易被封IP），我们设置 5 分钟缓存
CACHE_DATA = {
    "trends": [],
    "last_updated": 0
}

def get_real_time_trends():
    """
    统一入口：优先微博，失败转百度，带缓存机制
    """
    current_time = time.time()
    
    # 1. 检查缓存是否过期 (300秒 = 5分钟)
    if CACHE_DATA["trends"] and (current_time - CACHE_DATA["last_updated"] < 300):
        print("🚀 使用缓存热点数据")
        return CACHE_DATA["trends"]
    
    print("🌍 开始实时抓取热点...")
    
    # 2. 尝试抓取微博
    trends = scrape_weibo_hot_search()
    
    # 3. 如果微博挂了，尝试抓取百度
    if not trends:
        print("⚠️ 微博抓取为空，切换至百度源...")
        trends = scrape_baidu_hot_search()
    
    # 4. 更新缓存
    if trends:
        CACHE_DATA["trends"] = trends
        CACHE_DATA["last_updated"] = current_time
        return trends
    else:
        # 5. 如果全挂了，返回空列表（让调用方去使用 Mock 数据）
        return []