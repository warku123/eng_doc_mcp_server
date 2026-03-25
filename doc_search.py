"""文档搜索模块 - 提供三层降级搜索策略"""
import os
import json
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

# ReadMe 原生搜索 API（无需身份验证）
TRON_DOCS_SEARCH_API = "https://developers.tron.network/tron/api-next/v2/search"


async def search_docs_three_tier(
    query: str, 
    limit: int, 
    index_path: str, 
    base_url: str,
    enable_cache: bool = False,
    enable_api: bool = False
) -> str:
    """统一的三层文档搜索函数
    
    Args:
        query: 搜索关键词
        limit: 返回结果数量
        index_path: MkDocs 索引文件路径
        base_url: 文档基础 URL
        enable_cache: 是否启用本地缓存搜索（第2层）
        enable_api: 是否启用 ReadMe API 搜索（第3层）
    """
    if not query.strip():
        return "Error: Query is required."
    
    limit = min(max(limit, 1), 10)
    errors = []
    
    # 第1层：MkDocs 本地索引搜索（主要方案）
    if os.path.exists(index_path):
        try:
            result = perform_search(query, index_path, base_url, limit)
            if result and not result.startswith("Error") and result != "No relevant documentation found.":
                return result
        except Exception as e:
            errors.append(f"MkDocs index: {str(e)}")
    else:
        errors.append(f"MkDocs index: File not found at {index_path}")
    
    # 第2层：本地缓存搜索（可选）
    if enable_cache:
        try:
            return await search_via_local_cache(query, limit)
        except Exception as e:
            errors.append(f"Local cache: {str(e)}")
    
    # 第3层：ReadMe API 实时搜索（可选）
    if enable_api:
        try:
            return await search_via_readme_api(query, limit)
        except Exception as e:
            errors.append(f"ReadMe API: {str(e)}")
    
    # 所有方案都失败
    if errors:
        return f"Error searching documentation. All methods failed: {'; '.join(errors)}"
    return "No relevant documentation found."


def perform_search(query: str, index_path: str, base_url: str, limit: int = 5) -> str:
    """搜索本地 MkDocs 索引 - 基于分数的匹配"""
    if not os.path.exists(index_path):
        return "Error: Index not found. Run 'mkdocs build'."
    
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 按空格分词
    query_words = [w.strip() for w in query.lower().split() if len(w.strip()) > 1]
    if not query_words:
        query_words = [query.lower()]

    hits = []
    for doc in data['docs']:
        title_lower = doc['title'].lower()
        text_lower = doc.get('text', '').lower()
        
        # 分数匹配：标题命中 +3，内容命中 +1
        score = 0
        for word in query_words:
            if word in title_lower:
                score += 3
            if word in text_lower:
                score += 1
        
        if score > 0:
            excerpt = (doc.get('text') or '')[:200]
            hits.append((score, doc['title'], doc['location'], excerpt))
    
    # 按分数排序
    hits.sort(key=lambda x: x[0], reverse=True)
    
    if not hits:
        return "No relevant documentation found."
    
    # 取前 limit 个结果
    results = []
    for score, title, location, excerpt in hits[:limit]:
        results.append(f"### {title}\nURL: {base_url}{location}\nExcerpt: {excerpt}...")
    
    return "\n\n".join(results)


# ==================== 本地缓存搜索 ====================

# 缓存
_tron_docs_cache: List[Dict[str, Any]] = []
_tron_docs_cache_time: datetime = None
CACHE_TTL_SECONDS = 3600  # 1小时缓存


async def search_via_local_cache(query: str, limit: int) -> str:
    """通过本地缓存搜索（备用方案）"""
    from index_fetcher import fetch_all_tron_docs
    
    docs = await fetch_all_tron_docs()
    
    if not docs:
        return "Error: Failed to load documentation."
    
    # 简单搜索逻辑
    query_words = [w.strip().lower() for w in query.split() if len(w.strip()) > 1]
    if not query_words:
        query_words = [query.lower()]
    
    hits = []
    for doc in docs:
        title_lower = doc['title'].lower()
        text_lower = doc['text'].lower()
        
        score = 0
        for word in query_words:
            if word in title_lower:
                score += 3  # 标题匹配权重更高
            if word in text_lower:
                score += 1
        
        if score > 0:
            hits.append((score, doc))
    
    # 按分数排序
    hits.sort(key=lambda x: x[0], reverse=True)
    
    if not hits:
        return "No relevant documentation found."
    
    results = []
    for score, doc in hits[:limit]:
        excerpt = doc['text'][:200]
        url = f"https://developers.tron.network{doc['location']}"
        results.append(f"### {doc['title']}\nURL: {url}\nExcerpt: {excerpt}...")
    
    return f"## TRON Developer Docs Results ({len(results)} found, via local cache)\n\n" + "\n\n".join(results)


# ==================== ReadMe API 搜索 ====================

async def search_via_readme_api(query: str, limit: int) -> str:
    """通过 ReadMe 原生搜索 API 搜索（无需身份验证）"""
    params = {"query": query}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(TRON_DOCS_SEARCH_API, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        total = data.get("total", 0)
        hits = data.get("data", [])
        
        if not hits:
            return f"No results found for '{query}'."
        
        results = []
        for hit in hits[:limit]:
            title = hit.get("title", "Untitled")
            url = hit.get("url", {}).get("full", "")
            if not url:
                url = f"https://developers.tron.network{hit.get('url', {}).get('relative', '')}"
            
            # 从 highlights 提取摘要
            highlights = hit.get("highlights", [])
            excerpt_parts = []
            for h in highlights:
                if h.get("type") == "text":
                    excerpt_parts.append(h.get("value", ""))
            excerpt = " ".join(excerpt_parts)[:300]
            
            results.append(f"### {title}\nURL: {url}\nExcerpt: {excerpt}...")
        
        return f"## TRON Developer Docs Results ({min(len(hits), limit)} of {total} found)\n\n" + "\n\n".join(results)
