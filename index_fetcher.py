"""索引抓取模块 - 负责抓取 TRON 文档页面到本地缓存"""
import asyncio
import re
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from config import get_doc_source_config, get_cache_ttl

# 缓存存储
_docs_cache: Dict[str, Dict[str, Any]] = {}


async def fetch_all_docs(
    source_name: str,
    config_path: str = "./docs_config.yaml",
    force_refresh: bool = False
) -> List[Dict[str, Any]]:
    """
    抓取指定文档源的所有页面
    
    Args:
        source_name: 文档源名称（如 'tron_developers', 'java_tron'）
        config_path: 配置文件路径
        force_refresh: 是否强制刷新缓存
    
    Returns:
        文档列表
    """
    global _docs_cache
    
    # 检查缓存
    if not force_refresh and source_name in _docs_cache:
        cache_entry = _docs_cache[source_name]
        ttl = get_cache_ttl(config_path)
        if datetime.now() - cache_entry['time'] < timedelta(seconds=ttl):
            return cache_entry['data']
    
    # 获取配置
    config = get_doc_source_config(source_name, config_path)
    cache_config = config.get('cache_config', {})
    pages = cache_config.get('pages', [])
    base_url = cache_config.get('base_url', '')
    
    if not pages or not base_url:
        return []
    
    # 并发抓取页面
    semaphore = asyncio.Semaphore(3)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    async def fetch_single_page(client: httpx.AsyncClient, path: str) -> Dict[str, Any]:
        async with semaphore:
            url = f"{base_url}{path}"
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                html = response.text
                
                # 提取标题
                title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I)
                title = title_match.group(1).replace(" | TRON Developer Hub", "") if title_match else path
                
                # 提取主要内容
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
    
    # 复用 HTTP 客户端
    async with httpx.AsyncClient(timeout=15.0) as client:
        tasks = [fetch_single_page(client, path) for path in pages]
        results = await asyncio.gather(*tasks)
    
    # 过滤错误并更新缓存
    valid_results = [r for r in results if not r.get("error")]
    _docs_cache[source_name] = {
        'data': valid_results,
        'time': datetime.now()
    }
    
    return valid_results


async def fetch_all_tron_docs() -> List[Dict[str, Any]]:
    """
    向后兼容：抓取 TRON 开发者文档页面（默认使用 tron_developers 配置）
    """
    return await fetch_all_docs('tron_developers')
