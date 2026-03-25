"""索引抓取模块 - 负责抓取 TRON 文档页面到本地缓存"""
import asyncio
import re
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 缓存
_tron_docs_cache: List[Dict[str, Any]] = []
_tron_docs_cache_time: datetime = None
CACHE_TTL_SECONDS = 3600  # 1小时缓存


async def fetch_all_tron_docs() -> List[Dict[str, Any]]:
    """抓取所有 TRON 文档页面索引（用于本地搜索）"""
    global _tron_docs_cache, _tron_docs_cache_time
    
    # 检查缓存
    if _tron_docs_cache and _tron_docs_cache_time:
        if datetime.now() - _tron_docs_cache_time < timedelta(seconds=CACHE_TTL_SECONDS):
            return _tron_docs_cache
    
    # 关键文档页面列表
    key_pages = [
        "/docs/getting-start",
        "/docs/consensus",
        "/docs/resource-model",
        "/docs/tvm",
        "/docs/tron-ide",
        "/docs/build-a-web3-app",
        "/docs/networks",
        "/docs/introduction",
        "/docs/account",
        "/docs/transaction",
        "/docs/smart-contract",
        "/docs/trc10-token",
        "/docs/trc20-token",
        "/docs/super-representative",
        "/reference/json-rpc-api-overview",
    ]
    
    semaphore = asyncio.Semaphore(3)  # 限制并发
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    async def fetch_single_page(client: httpx.AsyncClient, path: str) -> Dict[str, Any]:
        async with semaphore:
            url = f"https://developers.tron.network{path}"
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                html = response.text
                
                # 提取标题
                title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I)
                title = title_match.group(1).replace(" | TRON Developer Hub", "") if title_match else path
                
                # 提取主要内容 (简单文本提取)
                content = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.I|re.S)
                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.I|re.S)
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()[:3000]
                
                return {
                    "title": title,
                    "location": path,
                    "text": content
                }
            except Exception as e:
                return {"title": path, "location": path, "text": "", "error": str(e)}
    
    # 复用 HTTP 客户端连接池
    async with httpx.AsyncClient(timeout=15.0) as client:
        tasks = [fetch_single_page(client, path) for path in key_pages]
        results = await asyncio.gather(*tasks)
    
    _tron_docs_cache = [r for r in results if not r.get("error")]
    _tron_docs_cache_time = datetime.now()
    
    return _tron_docs_cache
